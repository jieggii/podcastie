import asyncio
import typing

from aiogram.types import LinkPreviewOptions, Message
from podcastie_telegram_html.tags import link

from bot.aiogram_view.view import View

from .menu_view import MenuView


class StartView(View):
    _STICKER_FILE_ID = "CAACAgIAAxkBAAEtRB1mxaR_qC3fOUFt2QzPIlos1UI0XwACAQEAAladvQoivp8OuMLmNDUE"

    async def handle_entrypoint(
        self, event: Message, data: dict[str, typing.Any]
    ) -> None:
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

        menu_view = MenuView()
        await menu_view.handle_entrypoint(event, data)
