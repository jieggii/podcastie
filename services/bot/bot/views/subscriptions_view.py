import typing

from bot.aiogram_callback_view.callback_view import CallbackView

from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.aiogram_callback_view.util import answer_entrypoint_event, answer_callback_query_entrypoint_event
from bot.callback_data.entrypoints import PodcastViewEntrypointCallbackData
from bot.core.user import User
from bot.callback_data.entrypoints import MenuViewEntrypointCallbackData
from bot.core.podcast import Podcast

def _build_reply_markup(podcasts: list[Podcast]) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    for i, podcast in enumerate(podcasts):
        kbd.button(text=podcast.db_object.meta.title, callback_data=PodcastViewEntrypointCallbackData(edit_current_message=True, podcast_id=podcast.db_object.id))
    kbd.button(text="<< Back", callback_data=MenuViewEntrypointCallbackData(edit_current_message=True))

    # todo: smarter kbd layout
    # place two podcats per row
    # place one podcast per row if its title is longer than X
    # place "<< Back" button on a separate row
    kbd.adjust(2)

    return kbd.as_markup()

def _build_poor_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="<< Back", callback_data=MenuViewEntrypointCallbackData(edit_current_message=True))

    return kbd.as_markup()


_POOR_REPLY_MARKUP = _build_poor_reply_markup()


class SubscriptionsView(CallbackView):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        user: User = data["user"]

        subscriptions = await user.get_following_podcasts()
        if subscriptions:
            text = "Here are the podcasts you follow"
            markup = _build_reply_markup(subscriptions)
        else:
            text = "You don't follow any podcasts yet."
            markup = _POOR_REPLY_MARKUP

        await answer_callback_query_entrypoint_event(event, data, message_text=text, reply_markup=markup)
