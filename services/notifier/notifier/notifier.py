import asyncio
import time
import typing
from asyncio import Queue
from base64 import urlsafe_b64encode
from dataclasses import dataclass

import aiogram.exceptions
import aiohttp
import podcastie_rss
import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.enums.chat_action import ChatAction
from aiogram.types import Message, URLInputFile
from podcastie_database.models.podcast import Podcast, PodcastMetaPatch, generate_podcast_title_slug
from podcastie_database.models.user import User
from podcastie_telegram_html import components, tags, util
from podcastie_telegram_html.tags import link
from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars

from notifier.bot_session import LocalTelegramAPIAiohttpSession
from notifier.http_retryer import HTTPRetryer

_AUDIO_FILE_SIZE_LIMIT = 2000 * 1024 * 1024  # Max audio file size allowed by Telegram
_AUDIO_FILE_CHUNK_SIZE = 512 * 1024  # 512 kb

_AUDIO_FILE_DOWNLOAD_TIMEOUT = 20 * 60  # 20 min
_AUDIO_FILE_UPLOAD_TIMEOUT = 20 * 60  # 20 min


@dataclass
class Episode:
    title: str
    audio: podcastie_rss.AudioFile
    link: str | None  # Link to the specific episode
    description: str | None  # Description of the episode

    podcast_ppid: str
    podcast_title: str  # title of the podcast
    podcast_link: str | None  # link to the podcast's main page
    podcast_cover_url: str | None  # URL to the podcast's cover image

    recipient_user_ids: list[int]  # list of user IDs who are recipients of the episode

    audio_telegram_file_id: str | None = None  # Telegram file_id of the audio file


class Notifier:
    _poll_interval: int
    _log_broadcast_queue_size_interval: int

    _bot: Bot
    _http_retryer: HTTPRetryer
    _broadcast_queue: Queue[Episode]

    def __init__(self, bot_token: str, poll_interval: int):
        # dependencies:
        self._bot = Bot(
            session=LocalTelegramAPIAiohttpSession("http://telegram-bot-api:8081"),
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self._http_retryer = HTTPRetryer(interval=1, max_attempts=10)

        self._poll_interval = poll_interval
        self._log_broadcast_queue_size_interval = 5

        self._broadcast_queue: Queue[Episode] = Queue()

    async def poll_feeds_task(self) -> None:
        log = structlog.getLogger().bind(task="poll_feeds")

        while True:
            # get all podcasts stored in the database:
            podcasts = await Podcast.find().to_list()

            for podcast in podcasts:
                bind_contextvars(podcast=podcast.meta.title)

                # check if there are any followers:
                log.info(f"checking if podcast has followers")
                followers = await User.find(User.following_podcasts == podcast.id).to_list()
                if not followers:
                    # todo: delete podcasts that does not have followers
                    # for SOME amount of time
                    log.info("skip podcast as it has no followers")
                    continue

                # try to fetch podcast RSS feed:
                log.info(f"checking podcast RSS feed for new updates")
                feed: podcastie_rss.Feed | None = None
                try:
                    feed = await self._http_retryer.wrap(
                        podcastie_rss.fetch_feed,
                        kwargs={"url": podcast.feed_url},
                        retry_callback=lambda attempt, prev_e: log.warning(
                            "retrying to fetch RSS feed", attempt=attempt, e=prev_e
                        ),
                    )
                except Exception as e:
                    match e:
                        case aiohttp.ClientError():
                            log.warning(
                                f"http client error while attempting to read feed",
                                podcast_title=podcast.meta.title,
                                e=e,
                            )
                        case podcastie_rss.MalformedFeedFormatError():
                            log.warning(f"feed is malformed", podcast_title=podcast.meta.title, e=e)

                        case podcastie_rss.MissingFeedTitleError():
                            log.warning(f"feed did not pass validation", podcast_title=podcast.meta.title, e=e)

                        case _:
                            log.exception(
                                f"unexpected exception while attempting to read feed",
                                podcast_title=podcast.meta.title,
                                e=e,
                            )

                podcast.latest_episode_info.check_ts = int(time.time())
                podcast.latest_episode_info.check_success = bool(feed)
                await podcast.save()

                if feed is None:
                    log.warning("skip podcast as was not able to check its feed")
                    continue

                # update podcast metadata if it has changed:
                podcast_meta_patch: PodcastMetaPatch = {}
                if podcast.meta.title != feed.title:
                    log.info(f"update podcast title", new_title=feed.title)
                    podcast_meta_patch["new_title"] = feed.title
                    podcast_meta_patch["new_title_slug"] = generate_podcast_title_slug(feed.title)

                if podcast.meta.description != feed.description:
                    log.info(f"update podcast description", new_description_len=len(feed.description))
                    podcast_meta_patch["new_description"] = feed.description

                if podcast.meta.link != feed.link:
                    log.info(f"update podcast link", new_link=feed.link)
                    podcast_meta_patch["new_link"] = feed.link

                if podcast.meta.cover_url != feed.cover_url:
                    log.info(f"update podcast cover url", new_cover_url=feed.cover_url)
                    podcast_meta_patch["new_cover_url"] = feed.cover_url

                podcast_meta_patched = podcast.meta.patch(podcast_meta_patch)
                if podcast_meta_patched:
                    await podcast.save()

                # skip podcast if it does not have any episodes:
                if not feed.latest_episode:
                    log.debug(f"skip podcast as it has no episodes")
                    continue

                if (podcast.latest_episode_info.publication_ts is None) or (
                    feed.latest_episode.published > podcast.latest_episode_info.publication_ts
                ):
                    bind_contextvars(episode=feed.latest_episode.title)
                    log.info(f"new episode is out")

                    # update latest episode timestamp in the database:
                    podcast.latest_episode_info.publication_ts = feed.latest_episode.published
                    await podcast.save()

                    # skip episode if it does not contain title or audio file:
                    if not feed.latest_episode.title or not feed.latest_episode.audio_file:
                        log.info("skip episode because it does not contain title or audio")
                        continue

                    log.info("send episode to the BROADCAST queue")
                    episode = Episode(
                        title=feed.latest_episode.title,
                        audio=feed.latest_episode.audio_file,
                        link=feed.latest_episode.link,
                        description=feed.latest_episode.description,
                        podcast_ppid=podcast.ppid,
                        podcast_title=podcast.meta.title,
                        podcast_link=podcast.meta.link,
                        podcast_cover_url=feed.cover_url,
                        recipient_user_ids=[follower.user_id for follower in followers],
                    )
                    await self._broadcast_queue.put(episode)

                    clear_contextvars()

            clear_contextvars()
            log.info(f"task is sleeping", sleep_sec=self._poll_interval)
            await asyncio.sleep(self._poll_interval)

    async def broadcast_episodes_task(self) -> None:
        log = structlog.getLogger().bind(task="broadcast_episodes")

        while True:
            episode = await self._broadcast_queue.get()
            bind_contextvars(podcast=episode.podcast_title, episode=episode.title)

            log.info(f"start broadcasting")

            footer_links = [
                link("audio", episode.audio.url),
                components.start_bot_link(
                    "follow",
                    bot_username=(await self._bot.get_me()).username,
                    payload=episode.podcast_ppid,
                    encode_payload=True,
                )
            ]
            description = util.escape(episode.description) if episode.description else ""

            text = (
                f"🎉 {link(episode.podcast_title, episode.podcast_link)} "
                f"has published a new episode - {link(episode.title, episode.link)}\n"
                f"{tags.blockquote(description, expandable=len(description) > 800)}\n"  # todo: const magic number
                f"{components.footer(footer_links)}"
            )

            for user_id in episode.recipient_user_ids:
                bind_contextvars(user_id=user_id)

                # send text notification to the user:
                try:
                    await self._http_retryer.wrap(
                        self._bot.send_message,
                        kwargs={"chat_id": user_id, "text": text, "disable_web_page_preview": True},
                        retry_callback=lambda attempt, prev_e: log.warning(
                            "retrying to send text notification", attempt=attempt, e=prev_e
                        ),
                    )
                    log.info("sent text notification")
                except Exception as e:
                    match e:
                        case aiogram.exceptions.TelegramForbiddenError():
                            # todo: check if the user has blocked the bot for too long, delete them from the database
                            log.info("skipping recipient, he/she has blocked the bot")
                        case _:
                            log.exception(
                                "unexpected exception when sending text notification, skipping this recipient", e=e
                            )
                    continue

                if episode.audio.size > _AUDIO_FILE_SIZE_LIMIT:
                    log.info("episode audio size is too big, won't be sent")
                    continue

                # send "UPLOAD_DOCUMENT" chat action to the user:
                try:
                    await self._http_retryer.wrap(
                        self._bot.send_chat_action,  # todo: this sets status only for 5 seconds, repeat this request until audio is sent
                        kwargs={"chat_id": user_id, "action": ChatAction.UPLOAD_DOCUMENT},
                        retry_callback=lambda attempt, prev_e: log.warning(
                            "retrying to send chat action", attempt=attempt, e=prev_e
                        ),
                    )
                except Exception as e:
                    log.exception("unexpected exception when sending chat action", e=e)

                audio_file: str | None | URLInputFile = episode.audio_telegram_file_id
                if audio_file is None:  # use URL input file if no file_id stored yet
                    audio_file = URLInputFile(
                        episode.audio.url,
                        filename="Episode.mp3",
                        chunk_size=_AUDIO_FILE_CHUNK_SIZE,
                        timeout=_AUDIO_FILE_DOWNLOAD_TIMEOUT,
                    )

                try:
                    message: Message = await self._http_retryer.wrap(
                        self._bot.send_audio,
                        kwargs={
                            "chat_id": user_id,
                            "audio": audio_file,
                            "title": episode.title,
                            "performer": episode.podcast_title,
                            "thumbnail": URLInputFile(episode.podcast_cover_url) if episode.podcast_cover_url else None,
                            "request_timeout": _AUDIO_FILE_UPLOAD_TIMEOUT,  # todo: investigate if it's file upload timeout or just API call timeout
                        },
                        retry_callback=lambda attempt, prev_e: log.warning(
                            "retrying to send audio", attempt=attempt, e=prev_e
                        ),
                    )
                    log.info("sent audio file")

                    # remember Telegram file_id for the next time:
                    if not episode.audio_telegram_file_id:
                        episode.audio_telegram_file_id = message.audio.file_id

                except Exception as e:
                    # todo: handle aiogram.exceptions.TelegramForbiddenError here
                    log.exception("unexpected exception when sending audio file", e=e)

            unbind_contextvars("recipient_user_id")
            log.info("finish broadcasting")

    async def log_broadcast_queue_size_task(self) -> None:
        log = structlog.getLogger().bind(task="log_broadcast_queue_size_task")

        while True:
            log.debug(f"episodes waiting to be broadcasted: {self._broadcast_queue.qsize()}")
            await asyncio.sleep(self._log_broadcast_queue_size_interval)

    async def start(self) -> None:
        tasks = [
            self.poll_feeds_task(),
            self.broadcast_episodes_task(),
            self.log_broadcast_queue_size_task(),
        ]
        await asyncio.gather(*tasks)
