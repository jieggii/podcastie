import typing

from aiogram.types import CallbackQuery, InlineQueryResult, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import UnfollowViewEntrypointCallbackData, SubscriptionsViewEntrypointCallbackData, \
    PodcastViewEntrypointCallbackData, MenuViewEntrypointCallbackData
from bot.core.podcast import Podcast, PodcastNotFoundError
from podcastie_telegram_html.tags import bold


def _build_reply_markup(podcast_id: PydanticObjectId) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Yes", callback_data=SubscriptionsViewEntrypointCallbackData(unfollow_podcast_id=podcast_id))
    kbd.button(text="« Cancel", callback_data=PodcastViewEntrypointCallbackData(podcast_id=podcast_id))

    kbd.adjust(2)

    return kbd.as_markup()


def _build_failure_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="« Subscriptions", callback_data=SubscriptionsViewEntrypointCallbackData())

    return kbd.as_markup()

class UnfollowView(View):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        callback_data: UnfollowViewEntrypointCallbackData = data["callback_data"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
            text = f"Are you sure that you want to stop following {bold(podcast.db_object.meta.title)}?"
            markup = _build_reply_markup(podcast.db_object.id)

        except PodcastNotFoundError:
            text = "Podcast not found"
            markup = _build_failure_reply_markup()

        await event.message.edit_text(text, reply_markup=markup)
