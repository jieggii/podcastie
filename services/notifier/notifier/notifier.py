import asyncio
import datetime
from asyncio import Queue
from dataclasses import dataclass

import aiohttp
import podcastie_rss
import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InputFile, URLInputFile
from podcastie_database import Podcast, User
from telegram_text import Link

from notifier.audio_storage import AudioStorage

_AUDIO_FILE_TRANSFER_CHUNK_SIZE = 64 * 1024  # 64 kb
_AUDIO_FILE_DOWNLOAD_TIMEOUT = 20 * 60  # 20 min
_AUDIO_FILE_UPLOAD_TIMEOUT = 20 * 60  # 20 min


@dataclass
class Episode:
    title: str
    publication_date: datetime.datetime
    audio_file_url: str  # URL to audio file hosted by podcast provider

    recipient_user_ids: list[int]  # list of recipients of the episode

    podcast_title: str  # title of the podcast
    podcast_link: str  # link to the podcast
    podcast_cover_url: str | None  # podcast cover image

    link: str | None  # link to the episode
    description: str | None

    audio_file_downloaded_filename: str | None = None
    audio_file_compressed_filename: str | None = None

    audio_file_telegram_id: str | None = None  # telegram id of the file


class Notifier:
    bot: Bot
    audio_storage: AudioStorage
    feed_poll_interval: int
    max_audio_file_size: int

    download_episode_audio_queue: Queue[Episode]
    compress_episode_audio_queue: Queue[Episode]
    broadcast_episode_queue: Queue[Episode]

    def __init__(
        self,
        bot_token: str,
        audio_storage_path: str,
        feed_poll_interval: int,
        max_audio_file_size: int,  # max acceptable audio file size, bytes
    ):
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.audio_storage = AudioStorage(audio_storage_path)
        self.feed_poll_interval = feed_poll_interval
        self.max_audio_file_size = max_audio_file_size

        self.download_episode_audio_queue: Queue[Episode] = Queue()
        self.compress_episode_audio_queue: Queue[Episode] = Queue()
        self.broadcast_episode_queue: Queue[Episode] = Queue()

        self.http_session = aiohttp.ClientSession()

    async def poll_feeds_task(self):
        log = structlog.getLogger().bind(task="poll_feeds")

        while True:
            # get all podcasts stored in the database:
            podcasts = await Podcast.find().to_list()

            for podcast in podcasts:
                log = log.bind(podcast_title=podcast.title)

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
                    # short polling interval (for example, 1 min - 24 hours).
                    feed = await podcastie_rss.fetch_podcast(podcast.feed_url, max_episodes=1)

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
                if (not podcast.latest_episode_date) or (
                    latest_episode_meta.publication_date > podcast.latest_episode_date
                ):
                    log = log.bind(episode_title=latest_episode_meta.title)
                    log.info(f"podcast has a new episode out")

                    podcast.latest_episode_date = latest_episode_meta.publication_date
                    await podcast.save()

                    # skip episodes that are not suitable for broadcasting:
                    if not latest_episode_meta.title or not latest_episode_meta.audio_file:
                        log.info("skipping episode because it is not suitable for broadcasting")
                        continue

                    episode = Episode(
                        title=latest_episode_meta.title,
                        link=latest_episode_meta.link,
                        description=latest_episode_meta.description,
                        publication_date=latest_episode_meta.publication_date,
                        audio_file_url=latest_episode_meta.audio_file.url,
                        recipient_user_ids=[follower.user_id for follower in followers],
                        podcast_title=podcast.title,
                        podcast_link=podcast.link,
                        podcast_cover_url=feed.cover_url,
                    )

                    # decide episode's path to the user:
                    if latest_episode_meta.audio_file.size > self.max_audio_file_size:
                        # 1. The episode's audio file is larger than Telegram's limit.
                        # We need to download, compress, and then broadcast it.
                        log.info(f"episode audio needs compression, sending to the DOWNLOAD queue")
                        await self.download_episode_audio_queue.put(episode)
                    else:
                        # 2. The episode's audio file is within Telegram's limit.
                        # We can simply broadcast it directly.
                        log.info(f"episode audio is SMOL enough, sending to the BROADCAST queue")
                        await self.broadcast_episode_queue.put(episode)

            log.info(f"notifier sleeps for {self.feed_poll_interval} seconds")
            await asyncio.sleep(self.feed_poll_interval)

    async def download_audio_files_task(self):
        log = structlog.getLogger().bind(task="download_audio_files")

        while True:
            episode = await self.download_episode_audio_queue.get()

            log = log.bind(episode_title=episode.title)
            log.info(f"start downloading")  # todo: log progress while downloading
            original_filename = await self.audio_storage.download(
                url=episode.audio_file_url,
                chunk_size=_AUDIO_FILE_TRANSFER_CHUNK_SIZE,
                timeout=_AUDIO_FILE_DOWNLOAD_TIMEOUT,
            )
            episode.audio_file_downloaded_filename = original_filename

            log.info(f"finish downloading, sending to the COMPRESS queue")
            await self.compress_episode_audio_queue.put(episode)

    async def compress_audio_files_task(self):
        log = structlog.getLogger().bind(task="compress_audio_files")

        while True:
            episode = await self.compress_episode_audio_queue.get()

            log = log.bind(episode_title=episode.title)
            log.info(f"start compressing")
            compressed_filename = await self.audio_storage.compress_file(
                filename=episode.audio_file_downloaded_filename, target_size=self.max_audio_file_size
            )
            episode.audio_file_compressed_filename = compressed_filename

            log.info(f"finish compressing, sending to the BROADCAST queue")
            await self.broadcast_episode_queue.put(episode)

    async def broadcast_episodes_task(self):
        log = structlog.getLogger().bind(task="broadcast_episodes")

        while True:
            episode = await self.broadcast_episode_queue.get()

            log = log.bind(episode_title=episode.title)
            log.info(f"start broadcasting")
            fmt_podcast_title = Link(episode.podcast_title, episode.podcast_link).to_html()

            fmt_title = Link(episode.title, episode.link).to_html() if episode.link else episode.title
            fmt_description = episode.description if episode.description else "[no description available]"
            fmt_audio_file = Link("here", episode.audio_file_url).to_html()

            text = (
                f"{fmt_podcast_title} has published a new episode - {fmt_title}\n"
                "\n"
                f"{fmt_description}\n"
                "\n"
                f"📁 Download original episode audio {fmt_audio_file}."
            )

            audio_thumbnail: URLInputFile | None = (
                URLInputFile(episode.podcast_cover_url) if episode.podcast_cover_url else None
            )
            audio_filename = "Episode.mp3"

            for user_id in episode.recipient_user_ids:
                # send text notification to the user: (todo: try)
                await self.bot.send_message(user_id, text)

                # send audio file to the user:
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

                await self.bot.send_chat_action(
                    chat_id=user_id, action="upload_document"
                )  # todo: this sets status only for 5 seconds, repeat this request until audio is sent

                message = await self.bot.send_audio(  # todo: try
                    chat_id=user_id,
                    audio=audio_file,
                    title=episode.title,
                    performer=episode.podcast_title,
                    thumbnail=audio_thumbnail,
                    request_timeout=_AUDIO_FILE_UPLOAD_TIMEOUT,  # todo: investigate if it's file upload timeout or just API call timeout
                )

                # remember Telegram file_id for the next time:
                if not episode.audio_file_telegram_id:
                    episode.audio_file_telegram_id = message.audio.file_id

                log.info("finish broadcasting")

    async def run(self):
        await asyncio.gather(
            self.poll_feeds_task(),
            self.download_audio_files_task(),
            self.compress_audio_files_task(),
            self.broadcast_episodes_task(),
        )
