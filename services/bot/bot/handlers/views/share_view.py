import typing

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from podcastie_telegram_html.components import start_bot_url
from podcastie_telegram_html.tags import bold

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    PodcastViewEntrypointCallbackData,
    ShareViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
)
from bot.core.instant_link import build_instant_link
from bot.core.podcast import Podcast, PodcastNotFoundError


def _build_reply_markup(
    podcast_id: PydanticObjectId, podcast_title: str
) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(
        text="Share podcast to a Telegram chat", switch_inline_query=podcast_title
    )
    kbd.button(
        text="« Back",
        callback_data=PodcastViewEntrypointCallbackData(podcast_id=podcast_id),
    )
    kbd.adjust(1, 1)
    return kbd.as_markup()


def _build_failed_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(text="« Back", callback_data=SubscriptionsViewEntrypointCallbackData())
    return kbd.as_markup()


class ShareView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        bot: Bot = data["bot"]
        callback_data: ShareViewEntrypointCallbackData = data["callback_data"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
        except PodcastNotFoundError:
            await event.answer("Podcast not found.")  # todo emoji
            return

        instant_link = build_instant_link(
            bot_username=(await bot.get_me()).username,
            podcast_feed_url_hash_prefix=podcast.model.feed_url_hash_prefix,
        )
        text = (
            f"📤 Here are several ways to share {bold(podcast.model.meta.title)}:\n"
            "\n"
            f"{bold("Podcast website:")} {podcast.model.meta.link if podcast.model.meta.link else "not available"}\n"
            f"{bold("RSS feed:")} {podcast.model.feed_url}\n"
            f"{bold("Instant Link:")} {instant_link}"
        )
        markup = _build_reply_markup(podcast.model.id, podcast.model.meta.title)
        await event.message.edit_text(
            text,
            reply_markup=markup,
            link_preview_options=LinkPreviewOptions(
                is_disabled=False,
                url=podcast.model.meta.link,
                prefer_large_media=True,
            ),
        )
