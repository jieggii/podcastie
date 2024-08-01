from dataclasses import dataclass

from asyncio import Queue

from aiogram.exceptions import TelegramForbiddenError
import podcastie_rss
import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import URLInputFile, Message
from feed_poller.bot_session import LocalTelegramAPIAiohttpSession
from podcastie_telegram_html import util, tags
from podcastie_telegram_html.tags import link

from podcastie_database.models.podcast import Podcast

from feed_poller.http_retryer import HTTPRetryer
from podcastie_telegram_html import components
from structlog.contextvars import bind_contextvars, unbind_contextvars

_AUDIO_FILE_SIZE_LIMIT = 2000 * 1024 * 1024  # Max audio file size allowed by Telegram
_AUDIO_FILE_CHUNK_SIZE = 512 * 1024  # 512 kb

_AUDIO_FILE_DOWNLOAD_TIMEOUT = 20 * 60  # 20 min
_AUDIO_FILE_UPLOAD_TIMEOUT = 20 * 60  # 20 min


@dataclass
class Episode:
    recipient_user_ids: list[int]  # list of user IDs who are recipients of the episode

    title: str
    audio: podcastie_rss.AudioFile
    podcast: Podcast

    link: str | None
    description: str | None

    audio_telegram_file_id: str | None = None  # Telegram file_id of the audio file


class EpisodeBroadcaster:
    _bot: Bot
    _audio_file_size_limit: int

    _http_retryer: HTTPRetryer
    _episodes: Queue[Episode]

    _task_name = "episode_broadcaster"

    def __init__(self, bot_api_host: str, bot_api_port: int, bot_token: str):
        self._bot = Bot(
            token=bot_token,
            session=LocalTelegramAPIAiohttpSession(
                f"http://{bot_api_host}:{bot_api_port}",
            ),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self._http_retryer = HTTPRetryer(interval=1, max_attempts=10)
        self._episodes = Queue()

    async def add_episode(self, episode: Episode) -> None:
        await self._episodes.put(episode)

    async def run(self) -> None:
        log = structlog.getLogger().bind(task=self._task_name)

        while True:
            episode = await self._episodes.get()
            bind_contextvars(podcast=episode.podcast.meta.title, episode=episode.title)

            log.info(f"start broadcasting")

            footer_items = [
                link("audio", episode.audio.url),
                components.start_bot_link(
                    "follow",
                    bot_username=(await self._bot.get_me()).username,
                    payload=episode.podcast.ppid,
                    encode_payload=True,
                ),
                f"#{episode.podcast.meta.title_slug}"
            ]
            description = util.escape(episode.description) if episode.description else ""

            text = (
                f"🎉 {link(episode.podcast.meta.title, episode.podcast.meta.link)} "
                f"has published a new episode - {link(episode.title, episode.link)}\n"
                f"{tags.blockquote(description, expandable=len(description) > 800)}\n"  # todo: const magic number
                f"{components.footer(footer_items)}"
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
                        case TelegramForbiddenError():
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
                        self._bot.send_chat_action,  # todo: this sets status only for 5 seconds, repeat this request until audio is delivered
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
                        filename="Episode.mp3",  # todo: use actual file name
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
                            "performer": episode.podcast.meta.title,
                            "thumbnail": URLInputFile(episode.podcast.meta.cover_url) if episode.podcast.meta.cover_url else None,
                            "request_timeout": _AUDIO_FILE_UPLOAD_TIMEOUT,
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
