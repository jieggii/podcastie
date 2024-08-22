import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from podcastie_telegram_html.tags import blockquote, bold
from podcastie_telegram_html.util import escape

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    MenuViewEntrypointCallbackData,
    PodcastViewEntrypointCallbackData,
    ShareViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
    UnfollowViewEntrypointCallbackData,
)
from bot.core.podcast import Podcast, PodcastNotFoundError


def _build_reply_markup(podcast_id: PydanticObjectId) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="Unfollow",
        callback_data=UnfollowViewEntrypointCallbackData(podcast_id=podcast_id),
    )
    kbd.button(
        text="Share",
        callback_data=ShareViewEntrypointCallbackData(podcast_id=podcast_id),
    )

    kbd.button(text="« Back", callback_data=SubscriptionsViewEntrypointCallbackData())

    kbd.adjust(2, 1)

    return kbd.as_markup()


def _build_failure_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="« Back", callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()


class PodcastView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        callback_data: PodcastViewEntrypointCallbackData = data["callback_data"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
            meta = podcast.model.meta

            text = f"{bold(meta.title)}\n"
            if podcast.model.meta.description:
                escaped_description = escape(podcast.model.meta.description)
                expandable = len(escaped_description) > 1000
                text += blockquote(escaped_description, expandable=expandable)

            markup = _build_reply_markup(podcast.model.id)

            await event.message.edit_text(
                text,
                reply_markup=markup,
                link_preview_options=LinkPreviewOptions(
                    is_disabled=False,
                    url=podcast.model.meta.link,
                    prefer_small_media=True,
                ),
            )

        except PodcastNotFoundError:
            await event.message.edit_text(
                "⚠️ Podcast not found.", reply_markup=_build_failure_reply_markup()
            )
