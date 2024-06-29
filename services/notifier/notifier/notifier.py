import asyncio
from asyncio import Queue
from dataclasses import dataclass

import aiogram.exceptions
import aiohttp
import podcastie_rss
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.enums.chat_action import ChatAction
from aiogram.types import FSInputFile, InputFile, Message, URLInputFile
from podcastie_database import Podcast, User
from telegram_text import Link

from notifier.audio_storage import AudioStorage
from notifier.retry import retry_forever

_AUDIO_FILE_TRANSFER_CHUNK_SIZE = 512 * 1024  # 512 kb
_AUDIO_FILE_DOWNLOAD_TIMEOUT = 20 * 60  # 20 min
_AUDIO_FILE_UPLOAD_TIMEOUT = 20 * 60  # 20 min


@dataclass
class Episode:
    title: str
    publication_date: int
    audio_file_url: str  # URL to the audio file hosted by the podcast provider

    recipient_user_ids: list[int]  # list of user IDs who are recipients of the episode

    podcast_title: str  # title of the podcast
    podcast_link: str  # link to the podcast's main page
    podcast_cover_url: str | None  # URL to the podcast's cover image

    link: str | None  # Link to the specific episode
    description: str | None  # Description of the episode

    # indicates if the notifier should attempt to send the episode audio file. Set to False only when an error occurs while processing the audio file
    send_audio_file: bool = True

    audio_file_downloaded_filename: str | None = None  # Local filename of the downloaded audio file
    audio_file_compressed_filename: str | None = None  # Local filename of the compressed audio file

    audio_file_telegram_id: str | None = None  # Telegram file_id of the audio file


class Notifier:
    bot: Bot
    audio_storage: AudioStorage
    poll_feeds_http_session: aiohttp.ClientSession

    poll_feeds_interval: int
    log_queue_sizes_interval: int

    max_audio_file_size: int
    max_telegram_audio_file_size: int

    download_audio_queue: Queue[Episode]
    compress_audio_queue: Queue[Episode]
    broadcast_queue: Queue[Episode]

    def __init__(
        self,
        bot_token: str,
        audio_storage_path: str,
        poll_feeds_interval: int,
        log_queue_sizes_interval: int,
        max_audio_file_size: int,  # max acceptable audio file size for notifier, larger will not be handled
        max_telegram_audio_file_size: int,  # max acceptable audio file size for Telegram, larger will be compressed, bytes
    ):
        # dependencies:
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.audio_storage = AudioStorage(
            path=audio_storage_path,
            download_chunk_size=_AUDIO_FILE_TRANSFER_CHUNK_SIZE,
            download_timeout=_AUDIO_FILE_DOWNLOAD_TIMEOUT,
        )
        self.poll_feeds_http_session = aiohttp.ClientSession()

        # task intervals:
        self.poll_feeds_interval = poll_feeds_interval
        self.log_queue_sizes_interval = log_queue_sizes_interval

        # audio file size limit constants:
        self.max_audio_file_size = max_audio_file_size
        self.max_telegram_audio_file_size = max_telegram_audio_file_size

        # queues:
        self.download_audio_queue: Queue[Episode] = Queue()
        self.compress_audio_queue: Queue[Episode] = Queue()
        self.broadcast_queue: Queue[Episode] = Queue()

    async def poll_feeds_task(self):
        log = structlog.getLogger().bind(task="poll_feeds")

        while True:
            # get all podcasts stored in the database:
            podcasts = await Podcast.find().to_list()

            for podcast in podcasts:
                bind_contextvars(podcast_title=podcast.title)

                # check if there are any followers:
                log.info(f"checking if podcast has followers")
                followers = await User.find(User.following_podcasts == podcast.id).to_list()
                if not followers:  # skip and delete the podcast if it has no followers
                    log.info("skipping and deleting podcast that has no followers")
                    await podcast.delete()
                    continue

                # try to fetch podcast RSS feed:
                log.info(f"checking podcast RSS feed for updates")
                try:
                    # Personally I think, that fetching only one latest episode
                    # from the feed (i.e. having max_episodes=1) is enough as long as we have reasonably
                    # short polling interval (for example, 1 min - couple hours).
                    feed: podcastie_rss.Podcast = await retry_forever(
                        podcastie_rss.fetch_podcast,
                        kwargs={
                            "url": podcast.feed_url,
                            "max_episodes": 1,
                        },
                        on_retry=lambda attempt, prev_e: log.warning(
                            "retrying to fetch RSS feed", attempt=attempt, prev_e=prev_e
                        ),
                        exceptions=(aiohttp.ClientConnectionError,),
                        interval=1,
                    )

                except aiohttp.ClientError as e:
                    log.error(f"http client error while attempting to read feed", podcast_title=podcast.title, e=e)
                    continue

                except podcastie_rss.MalformedFeedFormatError as e:
                    log.error(f"failed to parse malformed feed content", podcast_title=podcast.title, e=e)
                    continue

                except podcastie_rss.FeedDidNotPassValidation as e:
                    log.error(f"feed did not pass validation {podcast} {e=}")
                    continue

                except Exception as e:
                    log.error(f"unexpected exception while attempting to read feed", podcast_title=podcast.title, e=e)
                    continue

                # update podcast metadata if it has changed:
                update_podcast = False
                if podcast.title != feed.title:
                    log.info(f"updating podcast title", new_podcast_title=feed.title)
                    update_podcast = True
                    podcast.title = feed.title

                if podcast.link != feed.link:
                    log.info(f"updating podcast link", new_podcast_link=feed.link)
                    update_podcast = True
                    podcast.link = feed.link

                if update_podcast:
                    log.info(f"storing new podcast meta")
                    await podcast.save()

                if not feed.episodes:  # skip feeds without any episodes
                    log.info(f"skipping podcast as it has no episodes")
                    continue

                latest_episode_meta = feed.episodes[0]
                if (not podcast.latest_episode_published) or (
                    latest_episode_meta.published > podcast.latest_episode_published
                ):
                    log = log.bind(episode_title=latest_episode_meta.title)
                    log.info(f"podcast has a new episode out")

                    podcast.latest_episode_published = latest_episode_meta.published
                    await podcast.save()

                    # skip episodes that are not suitable for broadcasting:
                    if not latest_episode_meta.title or not latest_episode_meta.audio_file:
                        log.info("skipping episode because it is not suitable for broadcasting")
                        continue

                    episode = Episode(
                        title=latest_episode_meta.title,
                        link=latest_episode_meta.link,
                        description=latest_episode_meta.description,
                        publication_date=latest_episode_meta.published,
                        audio_file_url=latest_episode_meta.audio_file.url,
                        recipient_user_ids=[follower.user_id for follower in followers],
                        podcast_title=podcast.title,
                        podcast_link=podcast.link,
                        podcast_cover_url=feed.cover_url,
                    )

                    # decide episode's path to the user:
                    if latest_episode_meta.audio_file.size > self.max_audio_file_size:
                        # 1. The episode's audio file is larger than notifier's limit.
                        # It will neither be handler nor sent to users
                        log.info(
                            "audio is too large for notifier, it will neither be handled nor sent to users, sending to BROADCAST queue",
                        )
                        episode.send_audio_file = False
                        await self.broadcast_queue.put(episode)

                    elif latest_episode_meta.audio_file.size > self.max_telegram_audio_file_size:
                        # 2. The episode's audio file is larger than Telegram's limit.
                        # We need to download, compress, and then broadcast it.
                        log.info(f"audio needs compression, sending to the DOWNLOAD queue")
                        await self.download_audio_queue.put(episode)
                    else:
                        # 3. The episode's audio file is within Telegram's limit.
                        # We can simply broadcast it directly.
                        log.info(f"audio is small enough, sending to the BROADCAST queue")
                        await self.broadcast_queue.put(episode)

            clear_contextvars()
            log.info(f"notifier sleeps for {self.poll_feeds_interval} seconds")
            await asyncio.sleep(self.poll_feeds_interval)

    async def download_audio_files_task(self):
        log = structlog.getLogger().bind(task="download_audio_files")

        while True:
            episode = await self.download_audio_queue.get()

            log = log.bind(podcast_title=episode.podcast_title, episode_title=episode.title)
            log.info(f"start downloading")

            try:
                original_filename: str = await retry_forever(
                    self.audio_storage.download,
                    kwargs={
                        "url": episode.audio_file_url,
                    },
                    on_retry=lambda attempt, prev_e: log.warning(
                        "retrying to download", attempt=attempt, prev_e=prev_e, url=episode.audio_file_url
                    ),
                    exceptions=(aiohttp.ClientConnectionError,),
                    interval=1,
                )
                episode.audio_file_downloaded_filename = original_filename

            except aiohttp.ClientError as e:
                episode.send_audio_file = False
                log.error("http client error when trying to download, episode audio will not be sent", e=e)

            except Exception as e:
                episode.send_audio_file = False
                log.error("unexpected exception when trying to download, episode audio will not be sent", e=e)

            log.info(f"finish DOWNLOAD task, sending to the COMPRESS queue")
            await self.compress_audio_queue.put(episode)

    async def compress_audio_files_task(self):
        log = structlog.getLogger().bind(task="compress_audio_files")

        while True:
            episode = await self.compress_audio_queue.get()

            log = log.bind(podcast_title=episode.podcast_title, episode_title=episode.title)  # todo: include filesize?
            log.info(f"start compressing")

            try:
                compressed_filename = await self.audio_storage.compress_file(
                    filename=episode.audio_file_downloaded_filename, target_size=self.max_telegram_audio_file_size
                )
                episode.audio_file_compressed_filename = compressed_filename
            except Exception as e:
                episode.send_audio_file = False
                log.error("unexpected exception when compressing, audio file will not be sent", e=e)

            log.info(f"finish COMPRESS task, sending to the BROADCAST queue")
            await self.broadcast_queue.put(episode)

    async def broadcast_episodes_task(self):
        log = structlog.getLogger().bind(task="broadcast_episodes")

        while True:
            episode = await self.broadcast_queue.get()

            log = log.bind(podcast_title=episode.podcast_title, episode_title=episode.title)
            log.info(f"start broadcasting")

            fmt_podcast_title = Link(episode.podcast_title, episode.podcast_link).to_html()

            fmt_title = Link(episode.title, episode.link).to_html() if episode.link else episode.title
            fmt_description = episode.description if episode.description else "[no description available]"
            fmt_audio_file = Link("here", episode.audio_file_url).to_html()

            text = (
                f"🎉 {fmt_podcast_title} has published a new episode - {fmt_title}\n"
                "\n"
                f"{fmt_description}\n"
                "\n"
                f"📁 Download original episode audio {fmt_audio_file}."
            )

            audio_thumbnail: URLInputFile | None = (
                URLInputFile(episode.podcast_cover_url) if episode.podcast_cover_url else None
            )
            audio_filename = "Episode.mp3"  # todo: new filename for new episode from audio URL

            for user_id in episode.recipient_user_ids:
                log = log.bind(recipient_user_id=user_id)

                # send text notification to the user:
                try:
                    await retry_forever(
                        self.bot.send_message,
                        kwargs={"chat_id": user_id, "text": text},
                        on_retry=lambda attempt, prev_e: log.warning(
                            "retrying to send text notification", attempt=attempt, prev_e=prev_e
                        ),
                        exceptions=(aiohttp.ClientConnectionError,),
                        interval=1,
                    )
                    log.info("sent text notification")

                except aiogram.exceptions.TelegramForbiddenError:
                    log.info("skipping recipient, he/she has blocked the bot")
                    # todo: check if the user has blocked the bot for too long, delete them from the database
                    continue

                except Exception as e:
                    log.error("unexpected exception when sending text notification, skipping this recipient", e=e)
                    continue

                # send uploading document chat action to the user:
                try:
                    await retry_forever(
                        self.bot.send_chat_action,  # todo: this sets status only for 5 seconds, repeat this request until audio is sent
                        kwargs={"chat_id": user_id, "action": ChatAction.UPLOAD_DOCUMENT},
                        on_retry=lambda attempt, prev_e: log.warning(
                            "retrying to send chat action", attempt=attempt, prev_e=prev_e
                        ),
                        exceptions=(aiohttp.ClientConnectionError,),
                        interval=1,
                    )
                except Exception as e:
                    log.error("unexpected exception when sending chat action", e=e)

                # send audio file to the user (if there were no problems with it):
                if episode.send_audio_file:
                    audio_file: InputFile | str
                    if episode.audio_file_telegram_id:
                        # use Telegram file_id as audio file if available
                        audio_file = episode.audio_file_telegram_id
                    elif episode.audio_file_compressed_filename:
                        # use locally stored compressed audio file if available
                        audio_file = FSInputFile(
                            path=self.audio_storage.get_file_path(episode.audio_file_compressed_filename),
                            filename=audio_filename,
                            chunk_size=_AUDIO_FILE_TRANSFER_CHUNK_SIZE,
                        )
                    else:
                        # use original audio file URL
                        audio_file = URLInputFile(
                            episode.audio_file_url,
                            filename=audio_filename,
                            chunk_size=_AUDIO_FILE_TRANSFER_CHUNK_SIZE,
                            timeout=_AUDIO_FILE_DOWNLOAD_TIMEOUT,
                        )

                    try:
                        message: Message = await retry_forever(
                            self.bot.send_audio,
                            kwargs={
                                "chat_id": user_id,
                                "audio": audio_file,
                                "title": episode.title,
                                "performer": episode.podcast_title,
                                "thumbnail": audio_thumbnail,
                                "request_timeout": _AUDIO_FILE_UPLOAD_TIMEOUT,  # todo: investigate if it's file upload timeout or just API call timeout
                            },
                            on_retry=lambda attempt, prev_e: log.warning(
                                "retrying to send audio", attempt=attempt, prev_e=prev_e
                            ),
                            exceptions=(aiohttp.ClientConnectionError,),
                            interval=1,
                        )
                        log.info("sent audio file")

                        # remember Telegram file_id for the next time:
                        if not episode.audio_file_telegram_id:
                            episode.audio_file_telegram_id = message.audio.file_id

                    except Exception as e:
                        log.error("unexpected exception when sending audio file", e=e)

            log.info("finish broadcasting")

    async def log_queue_sizes_task(self):
        log = structlog.getLogger().bind(task="log_queue_sizes")

        while True:
            log.debug(
                f"queue sizes: DOWNLOAD: {self.download_audio_queue.qsize()}, COMPRESS: {self.compress_audio_queue.qsize()} BROADCAST: {self.broadcast_queue.qsize()}"
            )
            await asyncio.sleep(self.log_queue_sizes_interval)

    async def run(self):
        tasks = [
            self.poll_feeds_task(),
            self.download_audio_files_task(),
            self.compress_audio_files_task(),
            self.broadcast_episodes_task(),
            self.log_queue_sizes_task(),
        ]
        await asyncio.gather(*tasks)

    async def close(self):
        await self.audio_storage.close()
        await self.poll_feeds_http_session.close()
