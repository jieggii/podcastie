import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from bot.aiogram_view.view import View
from bot.aiogram_view.util import answer_callback_query_entrypoint_event
from bot.callback_data.entrypoints import PodcastViewEntrypointCallbackData
from bot.callback_data.entrypoints import ShareViewEntrypointCallbackData
from bot.callback_data.entrypoints import SubscriptionsViewEntrypointCallbackData
from bot.core.podcast import Podcast, PodcastNotFoundError
from podcastie_telegram_html.tags import bold


def _build_reply_markup(podcast_id: PydanticObjectId) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(text="Share podcast to a Telegram chat", switch_inline_query="todo")
    kbd.button(text="« Back", callback_data=PodcastViewEntrypointCallbackData(podcast_id=podcast_id))
    kbd.adjust(1, 1)
    return kbd.as_markup()


def _build_failed_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(text="« Back", callback_data=SubscriptionsViewEntrypointCallbackData())
    return kbd.as_markup()


class ShareView(View):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        callback_data: ShareViewEntrypointCallbackData = data["callback_data"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
            text = (
                f"Here are useful ways to share {bold(podcast.db_object.meta.title)} with friends:\n"
                "\n"
                f"{bold("Podcast website:")} {podcast.db_object.meta.link if podcast.db_object.meta.link else "not available"}\n"
                f"{bold("RSS feed:")} {podcast.db_object.feed_url}\n"
                f"{bold("Instant Link:")} https://example.com"
            )
            markup = _build_reply_markup(podcast.db_object.id)
            await event.message.edit_text(
                text,
                reply_markup=markup,
                link_preview_options=LinkPreviewOptions(
                    is_disabled=False, url=podcast.db_object.meta.link, prefer_large_media=True
                ),
            )

        except PodcastNotFoundError:
            await event.message.edit_text("Podcast not found.", reply_markup=_build_reply_markup())
