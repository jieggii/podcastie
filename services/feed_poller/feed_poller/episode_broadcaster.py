import asyncio
from asyncio import Queue

import aiohttp
import structlog
from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_telegram_html import tags, util
from podcastie_telegram_html.tags import link
from structlog import contextvars
from tenacity import RetryError, retry, retry_if_exception_type, wait_exponential

from feed_poller.episode import Episode

_AUDIO_SIZE_LIMIT = 2000 * 1024 * 1024  # max audio file size allowed by Telegram (bytes)
_AUDIO_FILE_DOWNLOAD_TIMEOUT = 20 * 60  # timeout for audio download (seconds)
_AUDIO_FILE_UPLOAD_TIMEOUT = 20 * 60  # timeout for audio upload (seconds)

_DEFAULT_UPLOAD_AUDIO_CHUNK_SIZE = 512 * 1024  # chunk size for audio upload to Telegram (bytes)


class EpisodeNotificationSender:
    _bot: Bot
    _episode: Episode
    _notification_text: str

    _cached_episode_audio_telegram_file_id: str | None
    _cached_audio_message_inline_markup: InlineKeyboardMarkup | None

    def __init__(self, bot: Bot, episode: Episode):
        self._bot = bot
        self._episode = episode

        self._notification_text = self.build_notification_text(episode)

        self._cached_episode_audio_telegram_file_id = None
        self._cached_audio_message_inline_markup = None

    @staticmethod
    def build_notification_text(episode: Episode) -> str:
        text = (
            f"🎉 {link(episode.published_by.document.meta.title, episode.published_by.document.meta.link)} "
            f"published a new episode - {link(episode.title, episode.link)}"
        )

        if episode.description:
            escaped_description = util.escape(episode.description)
            text += "\n" f"{tags.blockquote(escaped_description, expandable=True)}"

        return text

    async def send_notification(self, user_id: int, upload_audio_chunk_size: int):
        await self._send_text_notification(user_id)
        await self._send_uploading_file_chat_action(user_id)

        if self._episode.audio.size > _AUDIO_SIZE_LIMIT:
            await self._send_audio_message(user_id)
        else:
            await self._send_audio_file(user_id, upload_audio_chunk_size)

    @retry(retry=retry_if_exception_type(aiohttp.ClientConnectorError), wait=wait_exponential(max=60))
    async def _send_text_notification(self, user_id: int):
        await self._bot.send_message(user_id, self._notification_text)

    @retry(retry=retry_if_exception_type(aiohttp.ClientConnectorError), wait=wait_exponential(max=60))
    async def _send_uploading_file_chat_action(self, user_id: int):
        await self._bot.send_chat_action(user_id, ChatAction.UPLOAD_DOCUMENT)

    @retry(retry=retry_if_exception_type(aiohttp.ClientConnectorError), wait=wait_exponential(max=60))
    async def _send_audio_file(self, user_id: int, upload_audio_chunk_size: int):
        file: str | URLInputFile
        if self._cached_episode_audio_telegram_file_id:
            file = self._cached_episode_audio_telegram_file_id
        else:
            file = URLInputFile(
                self._episode.audio.url,
                filename="Episode.mp3",
                chunk_size=upload_audio_chunk_size,
                timeout=_AUDIO_FILE_DOWNLOAD_TIMEOUT,
            )

        thumbnail: URLInputFile | None = None
        if self._episode.published_by.document.meta.cover_url:
            thumbnail = URLInputFile(self._episode.published_by.document.meta.cover_url)

        await self._bot.send_audio(
            user_id,
            file,
            performer=self._episode.published_by.document.meta.title,
            title=self._episode.title,
            thumbnail=thumbnail,
            disable_notification=True,
            request_timeout=_AUDIO_FILE_UPLOAD_TIMEOUT,  # todo: investigate
        )

    @retry(retry=retry_if_exception_type(aiohttp.ClientConnectorError), wait=wait_exponential(max=60))
    async def _send_audio_message(self, user_id: int):
        if not self._cached_audio_message_inline_markup:
            kbd = InlineKeyboardBuilder()
            kbd.button(text="Download episode audio", url=self._episode.audio.url)
            self._cached_audio_message_inline_markup = kbd.as_markup()

        await self._bot.send_message(
            user_id,
            f"The episode audio file size exceeds Telegram limits, "
            f"so I am not able to send it to you.\n"
            f"Instead, you can download it manually",
            reply_markup=self._cached_audio_message_inline_markup,
            disable_notification=True,
        )


class EpisodeBroadcaster:
    _bot: Bot
    _audio_file_size_limit: int
    _interval: int
    _upload_audio_chunk_size: int

    def __init__(
        self,
        episodes_queue: Queue[Episode],
        bot: Bot,
        interval: int,
        upload_audio_chunk_size: int = _DEFAULT_UPLOAD_AUDIO_CHUNK_SIZE,
    ):
        self._episodes_queue = episodes_queue
        self._bot = bot
        self._interval = interval
        self._upload_audio_chunk_size = upload_audio_chunk_size

    async def broadcast_episodes(self) -> None:
        log: structlog.stdlib.BoundLogger = structlog.get_logger(task=self.__class__.__name__)

        while True:
            episode = await self._episodes_queue.get()

            with contextvars.bound_contextvars(episode=episode.title, podcast=episode.published_by.document.meta.title):
                log.info("start broadcasting")

                notification_sender = EpisodeNotificationSender(self._bot, episode)

                for user in episode.recipients:
                    with contextvars.bound_contextvars(user_id=user.document.user_id):
                        try:
                            await notification_sender.send_notification(
                                user.document.user_id, self._upload_audio_chunk_size
                            )
                        except TelegramForbiddenError:
                            log.info("skipping user as they blocked the bot")
                            continue
                        except RetryError:
                            log.info("skipping user as retrying failed")
                            continue
                        except Exception as e:
                            log.error(f"unexpected exception when sending notification: {e}")
                            continue

                    log.info("sent new episode notification to user")

            log.info("finish broadcasting")
            log.info(f"task is sleeping for {self._interval} seconds")
            await asyncio.sleep(self._interval)
