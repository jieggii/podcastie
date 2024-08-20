import io
import typing

from aiogram import Bot
from aiogram.enums import ContentType, ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.aiogram_callback_view.callback_view import CallbackView
from bot.aiogram_callback_view.util import answer_callback_query_entrypoint_event, answer_entrypoint_event
from bot.callback_data.entrypoints import MenuViewEntrypointCallbackData

from bot.callback_data.entrypoints import ImportViewEntrypointCallbackData
from bot.core import opml
from bot.core.podcast import Podcast, PodcastNotFoundError, PodcastFeedError
from bot.core.user import User, UserFollowsPodcastError
from bot.fsm import BotState
from bot.validators import is_feed_url
from podcastie_telegram_html.tags import link


def _build_entrypoint_query_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="« Back to menu", callback_data=MenuViewEntrypointCallbackData(clear_state=True))

    return kbd.as_markup()

def _build_entrypoint_command_reply_markup() -> InlineKeyboardMarkup:
    pass


def _build_result_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Try again", callback_data=ImportViewEntrypointCallbackData(edit_current_message=True))
    kbd.button(text="<< Menu", callback_data=MenuViewEntrypointCallbackData(edit_current_message=True))

    return kbd.as_markup()


async def _follow_podcasts(user: User, feed_urls: list[str]) -> tuple[list[Podcast], list[tuple[Podcast | str, str]]]:
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
            await user.follow_podcast(podcast)
        except UserFollowsPodcastError:
            failed_to_follow.append((podcast, "you already follow this podcast"))
            continue

        followed.append(podcast)

    return followed, failed_to_follow


class ImportView(CallbackView):
    _FILE_SIZE_LIMIT = 1 * 1024 * 1024  # file size limit in bytes
    _FEED_URLS_LIMIT = 20

    _ENTRYPOINT_MARKUP = _build_entrypoint_query_reply_markup()

    async def handle_entrypoint(self, event: Message | CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        state: FSMContext = data["state"]

        await state.set_state(BotState.IMPORT)

        text = (
            "Please either attach an OPML file containing your subscriptions or "
            "send a text message containing podcast RSS feed URLs you want to follow."
        )
        markup = self._ENTRYPOINT_MARKUP

        await answer_entrypoint_event(event, data, message_text=text, query_answer_text=text, reply_markup=markup)

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        bot: Bot = data["bot"]
        user: User = data["user"]

        await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

        feed_urls: list[str]
        match message.content_type:
            case ContentType.TEXT:
                feed_urls = message.text.split()

            case ContentType.DOCUMENT:
                file = await bot.get_file(message.document.file_id)
                if file.file_size > self._FILE_SIZE_LIMIT:
                    await message.answer(
                        "⚠  The provided file exceeds file size limit.", reply_markup=_build_result_reply_markup(),
                    )
                    return

                content = io.BytesIO()
                await bot.download_file(file.file_path, content)

                try:
                    feed_urls = opml.parse_opml(content.read())
                except opml.OPMLParseError:
                    await message.answer(
                        "⚠  Failed to parse this OPML file.",
                        reply_markup=_build_result_reply_markup()
                    )
                    return

            case _:
                await message.answer(
                    "This message kind is not supported.", reply_markup=_build_result_reply_markup(),
                )
                return

        if len(feed_urls) > self._FEED_URLS_LIMIT:
            await message.answer("Number of RSS feed URLs exceeds the limit.", reply_markup=_build_result_reply_markup())

        # remove duplicated feed URLs
        feed_urls = list(set(feed_urls))

        followed, failed_to_follow = await _follow_podcasts(user, feed_urls)

        text = ""
        if followed:
            if failed_to_follow:
                text += "✨ You have successfully subscribed to the following podcasts:\n"
            else:
                text += "✨ You have successfully subscribed to all the provided podcasts:\n"

            for podcast in followed:
                text += f"- {link(podcast.db_object.meta.title, podcast.db_object.meta.link)}\n"

        if failed_to_follow:
            text += "\n"

            if followed:
                text += "Failed to subscribe the following podcasts:\n"
            else:
                text += "Failed to subscribe to any of the provided podcasts:\n"

            for podcast_or_feed_url, error_message in failed_to_follow:
                if isinstance(podcast_or_feed_url, Podcast):
                    text += f"⚠️ {link(podcast_or_feed_url.db_object.meta.title, podcast_or_feed_url.db_object.meta.link)}: {error_message}\n"
                elif isinstance(podcast_or_feed_url, str):
                    text += f"⚠️ {podcast_or_feed_url}: {error_message}\n"
                else:
                    raise ValueError("unexpected type of podcast_or_feed_url")

        await message.answer(text, reply_markup=_build_result_reply_markup())