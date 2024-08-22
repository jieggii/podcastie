import asyncio
import base64
import binascii
import typing

from aiogram.types import LinkPreviewOptions, Message
from podcastie_telegram_html.tags import bold
from podcastie_telegram_html.tags import link

from bot.aiogram_view.view import View

from bot.handlers.views.menu_view import MenuView
from bot.core.user import User, UserFollowsPodcastError
from bot.core.podcast import Podcast, PodcastNotFoundError


def _extract_payload(message_text: str) -> str | None:
    tokens = message_text.split(maxsplit=2)
    if len(tokens) != 2:
        return None

    feed_url_hash_prefix_encoded = tokens[1]
    feed_url_hash_prefix = base64.urlsafe_b64decode(feed_url_hash_prefix_encoded.encode()).decode()

    return feed_url_hash_prefix


class StartView(View):
    _STICKER_FILE_ID = (
        "CAACAgIAAxkBAAEtRB1mxaR_qC3fOUFt2QzPIlos1UI0XwACAQEAAladvQoivp8OuMLmNDUE"
    )

    async def handle_entrypoint(
        self, event: Message, data: dict[str, typing.Any]
    ) -> None:
        user: User | None = data["user"]
        is_new_user = user is None

        feed_url_hash_prefix: str | None = None
        try:
            feed_url_hash_prefix = _extract_payload(event.text)
        except binascii.Error:
            await event.answer("⚠️ Failed to decode podcast identifier provided using Instant Link.")

        if feed_url_hash_prefix:
            user = user or await User.new_from_user_id(event.from_user.id)

            podcast: Podcast | None = None
            try:
                podcast = await Podcast.from_feed_url_hash_prefix(feed_url_hash_prefix)
            except PodcastNotFoundError:
                await event.answer("⚠️ Podcast you are trying to follow using Instant Link does not exist.")

            if podcast:
                try:
                    await user.follow_podcast(podcast)
                except UserFollowsPodcastError:
                    await event.answer(f"⚠️ You already follow {bold(podcast.db_object.meta.title)}.")
                else:
                    await event.answer(f"🌟 You have successfully subscribed to {bold(podcast.db_object.meta.title)}.")

        if is_new_user or not feed_url_hash_prefix:
            text = (
                f"👋 Hi there, {event.from_user.first_name}!\n"
                f"\n"
                f"I'm {link("Podcastie Bot", "https://t.me/podcastie_bot")}, "
                "and I'm here to help you stay updated with your favorite podcasts! 🎧\n"
                "\n"
                "To get started, simply use the menu below.\n"
            )

            await event.answer(
                text,
                link_preview_options=LinkPreviewOptions(
                    is_disabled=False,
                    prefer_small_media=True,
                ),
            )

            await event.answer_sticker(self._STICKER_FILE_ID)

            await asyncio.sleep(1)

        await MenuView().handle_entrypoint(event, data)
