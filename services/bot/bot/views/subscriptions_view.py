import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_telegram_html.tags import bold

from bot.aiogram_view.util import (
    answer_callback_query_entrypoint_event,
    answer_entrypoint_event,
)
from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    MenuViewEntrypointCallbackData,
    PodcastViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
)
from bot.core.podcast import Podcast, PodcastNotFoundError
from bot.core.user import User, UserDoesNotFollowPodcastError


def _build_reply_markup(podcasts: list[Podcast]) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    for i, podcast in enumerate(podcasts):
        kbd.button(
            text=podcast.db_object.meta.title,
            callback_data=PodcastViewEntrypointCallbackData(
                edit_current_message=True, podcast_id=podcast.db_object.id
            ),
        )
    kbd.button(
        text="« Back",
        callback_data=MenuViewEntrypointCallbackData(edit_current_message=True),
    )

    # todo: smarter kbd layout
    # place two podcats per row
    # place one podcast per row if its title is longer than X
    # place "« Back" button on a separate row
    kbd.adjust(2)

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
                    await user.unfollow_podcast(podcast)
                    await event.answer(
                        f"Successfully unfollowed {podcast.db_object.meta.title}"
                    )
                except UserDoesNotFollowPodcastError:
                    await event.answer(
                        "Failed to unfollow podcast as you do not follow it anymore."
                    )
            except PodcastNotFoundError:
                await event.answer(
                    "Failed to unfollow podcast as it does not longer exist."
                )

        subscriptions = await user.get_following_podcasts()
        if subscriptions:
            text = "Here are the podcasts you follow"
            markup = _build_reply_markup(subscriptions)
        else:
            text = "You don't follow any podcasts yet."
            markup = _POOR_REPLY_MARKUP

        await event.message.edit_text(text, reply_markup=markup)
