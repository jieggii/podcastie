import io
import typing

from aiogram import Bot
from aiogram.enums import ChatAction, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_telegram_html.tags import link

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    ImportViewEntrypointCallbackData,
    MenuViewEntrypointCallbackData,
)
from bot.utils import opml
from podcastie_core.podcast import Podcast, PodcastFeedError, PodcastNotFoundError
from podcastie_core.user import User, UserFollowsPodcastError
from podcastie_core.service import follow_podcast
from bot.fsm import BotState
from bot.validators import is_feed_url


def _build_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="« Back to menu",
        callback_data=MenuViewEntrypointCallbackData(clear_state=True),
    )

    return kbd.as_markup()


def _build_result_reply_markup(failure: bool = False) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="Try again" if failure else "Import again",
        callback_data=ImportViewEntrypointCallbackData(edit_current_message=True),
    )
    kbd.button(
        text="« Menu",
        callback_data=MenuViewEntrypointCallbackData(edit_current_message=True),
    )

    return kbd.as_markup()


async def _follow_podcasts(
    user: User, feed_urls: list[str]
) -> tuple[list[Podcast], list[tuple[Podcast | str, str]]]:
    followed: list[Podcast] = []
    failed_to_follow: list[tuple[Podcast | str, str]] = []

    for url in feed_urls:
        if not is_feed_url(url):
            failed_to_follow.append((url, "invalid URL"))
            continue

        try:
            podcast = await Podcast.from_feed_url(url)
        except PodcastNotFoundError:
            try:
                podcast = await Podcast.new_from_feed_url(url)
            except PodcastFeedError:
                failed_to_follow.append((url, "failed to fetch RSS feed"))
                continue

        try:
            await follow_podcast(user, podcast)
        except UserFollowsPodcastError:
            failed_to_follow.append((podcast, "you already follow this podcast"))
            continue

        followed.append(podcast)

    return followed, failed_to_follow


class ImportView(View):
    _FILE_SIZE_LIMIT = 1 * 1024 * 1024  # file size limit in bytes
    _FEED_URLS_LIMIT = 20  # number of feed URLs limit

    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        state: FSMContext = data["state"]

        await state.set_state(BotState.IMPORT)

        text = (
            "📄 Attach an OPML file with your subscriptions or "
            "provide podcast RSS feed URLs in a text message to follow new podcasts."
        )
        await event.message.edit_text(text, reply_markup=_build_reply_markup())

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        state: FSMContext = data["state"]
        bot: Bot = data["bot"]
        user: User = data["user"]

        await state.clear()

        await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

        feed_urls: list[str]
        match message.content_type:
            case ContentType.TEXT:
                feed_urls = message.text.split()

            case ContentType.DOCUMENT:
                file = await bot.get_file(message.document.file_id)
                if file.file_size > self._FILE_SIZE_LIMIT:
                    await message.answer(
                        "⚠  The provided file exceeds file size limit.",
                        reply_markup=_build_result_reply_markup(failure=True),
                    )
                    return

                content = io.BytesIO()
                await bot.download_file(file.file_path, content)

                try:
                    feed_urls = opml.parse_opml(content.read())
                except opml.OPMLParseError:
                    await message.answer(
                        "⚠  Failed to parse this OPML file.",
                        reply_markup=_build_result_reply_markup(failure=True),
                    )
                    return

            case _:
                await message.answer(
                    "⚠️ This message kind is not supported.",
                    reply_markup=_build_result_reply_markup(failure=True),
                )
                return

        if len(feed_urls) > self._FEED_URLS_LIMIT:
            await message.answer(
                "⚠️ Number of RSS feed URLs exceeds the limit.",
                reply_markup=_build_result_reply_markup(failure=True),
            )

        if not feed_urls:
            await message.answer(
                "⚠️ The provided OPML file does not contain any subscriptions.",
                reply_markup=_build_result_reply_markup(failure=True)
            )
            return

        # remove duplicated feed URLs
        feed_urls = list(set(feed_urls))
        followed, failed_to_follow = await _follow_podcasts(user, feed_urls)

        text = ""
        if followed:
            if failed_to_follow:
                text += (
                    "✨ You have successfully subscribed to the following podcasts:\n\n"
                )
            else:
                text += "✨ You have successfully subscribed to all the provided podcasts:\n\n"

            for podcast in followed:
                text += f"- {link(podcast.document.meta.title, podcast.document.meta.link)}\n"

        if failed_to_follow:
            text += "\n"

            if followed:
                text += "Failed to subscribe to the following podcasts:\n\n"
            else:
                text += "Failed to subscribe to any of the provided podcasts:\n\n"

            for podcast_or_feed_url, error_message in failed_to_follow:
                if isinstance(podcast_or_feed_url, Podcast):
                    text += f"⚠️ {link(podcast_or_feed_url.document.meta.title, podcast_or_feed_url.document.meta.link)}: {error_message}\n"
                elif isinstance(podcast_or_feed_url, str):
                    text += f"⚠️ {podcast_or_feed_url}: {error_message}\n"
                else:
                    raise ValueError("unexpected type of podcast_or_feed_url")

        await message.answer(text, reply_markup=_build_result_reply_markup())
