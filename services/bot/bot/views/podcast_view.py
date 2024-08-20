import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from bot.aiogram_callback_view.callback_view import CallbackView
from bot.aiogram_callback_view.util import answer_callback_query_entrypoint_event
from bot.callback_data.entrypoints import PodcastViewEntrypointCallbackData
from bot.callback_data.entrypoints import ShareViewEntrypointCallbackData
from bot.callback_data.entrypoints import SubscriptionsViewEntrypointCallbackData
from bot.callback_data.entrypoints import MenuViewEntrypointCallbackData
from bot.core.podcast import Podcast
from podcastie_telegram_html.tags import bold, blockquote
from podcastie_telegram_html.util import escape

def _build_podcast_reply_markup(podcast_id: PydanticObjectId) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Unfollow", callback_data="todo")
    kbd.button(text="Share", callback_data=ShareViewEntrypointCallbackData(podcast_id=podcast_id))

    kbd.button(text="<< Back", callback_data=SubscriptionsViewEntrypointCallbackData())

    kbd.adjust(2, 1)

    return kbd.as_markup()

def _build_failure_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="<< Back", callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()


class PodcastView(CallbackView):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        callback_data: PodcastViewEntrypointCallbackData = data["callback_data"]

        podcast = await Podcast.from_object_id(callback_data.podcast_id)
        if podcast:
            meta = podcast.db_object.meta

            text = f"{bold(meta.title)}\n"
            if podcast.db_object.meta.description:
                escaped_description = escape(podcast.db_object.meta.description)
                expandable = len(escaped_description) > 1000
                text += blockquote(escaped_description, expandable=expandable)

            markup = _build_podcast_reply_markup(podcast.db_object.id)

        else:
            text = "Podcast not found"
            markup = _build_failure_reply_markup()

        await answer_callback_query_entrypoint_event(event, data, message_text=text, reply_markup=markup)
