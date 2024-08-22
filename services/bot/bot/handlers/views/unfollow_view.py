import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineQueryResult
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from podcastie_telegram_html.tags import bold

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    MenuViewEntrypointCallbackData,
    PodcastViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
    UnfollowViewEntrypointCallbackData,
)
from bot.core.podcast import Podcast, PodcastNotFoundError


def _build_reply_markup(podcast_id: PydanticObjectId) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="Yes",
        callback_data=SubscriptionsViewEntrypointCallbackData(
            unfollow_podcast_id=podcast_id
        ),
    )
    kbd.button(
        text="« Cancel",
        callback_data=PodcastViewEntrypointCallbackData(podcast_id=podcast_id),
    )

    kbd.adjust(2)

    return kbd.as_markup()


class UnfollowView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        callback_data: UnfollowViewEntrypointCallbackData = data["callback_data"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
        except PodcastNotFoundError:
            await event.answer("⚠️Podcast not found.", show_alert=True)
            return

        await event.message.edit_text(
            f"🔕 Are you sure that you want to stop following {bold(podcast.model.meta.title)}?",
            reply_markup=_build_reply_markup(podcast.model.id),
        )
