import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    MenuViewEntrypointCallbackData,
    PodcastViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
)
from podcastie_core.podcast import Podcast, PodcastNotFoundError
from podcastie_core.user import User, UserDoesNotFollowPodcastError


def _build_reply_markup(podcasts: list[Podcast]) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    for i, podcast in enumerate(podcasts):
        kbd.button(
            text=podcast.model.meta.title,
            callback_data=PodcastViewEntrypointCallbackData(
                edit_current_message=True, podcast_id=podcast.model.id
            ),
        )

    kbd.button(
        text="« Back",
        callback_data=MenuViewEntrypointCallbackData(edit_current_message=True),
    )

    kbd.adjust(1)

    return kbd.as_markup()


def _build_poor_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="« Back",
        callback_data=MenuViewEntrypointCallbackData(edit_current_message=True),
    )

    return kbd.as_markup()


_POOR_REPLY_MARKUP = _build_poor_reply_markup()


class SubscriptionsView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        callback_data: SubscriptionsViewEntrypointCallbackData = data["callback_data"]
        user: User = data["user"]

        if callback_data.unfollow_podcast_id:
            try:
                podcast = await Podcast.from_object_id(
                    callback_data.unfollow_podcast_id
                )
                try:
                    await user.unfollow(podcast)
                    await event.answer(
                        f"🔕 Successfully unfollowed {podcast.model.meta.title}."
                    )
                except UserDoesNotFollowPodcastError:
                    await event.answer(
                        f"⚠️ Failed to unfollow {podcast.model.meta.title} as you do not follow it anymore."
                    )
            except PodcastNotFoundError:
                await event.answer(
                    f"⚠️ Failed to unfollow podcast as it no longer exists."
                )

        subscriptions = await user.subscriptions()
        if not subscriptions:
            await event.message.edit_text(
                "🔕 You aren't following any podcasts yet.",
                reply_markup=_build_reply_markup(subscriptions),
            )
            return

        await event.message.edit_text(
            "📝 Here is the list of the podcasts you follow:",
            reply_markup=_build_reply_markup(subscriptions),
        )
