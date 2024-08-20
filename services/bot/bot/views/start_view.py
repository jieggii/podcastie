import typing

from aiogram.types import CallbackQuery, Message
from podcastie_telegram_html.tags import link

from bot.aiogram_view.view import View


class StartView(View):
    async def handle_entrypoint(
        self, event: Message, data: dict[str, typing.Any]
    ) -> None:
        text = (
            f"👋 Hi there, {event.from_user.first_name}!\n"
            f"\n"
            f"I'm {link("Podcastie Bot", "https://t.me/podcastie_bot")}, "
            "and I'm here to help you stay updated with your favorite podcasts! 🎧\n"
            "\n"
            "To get started, simply use the /menu command.\n"
        )
        await event.answer(text)
