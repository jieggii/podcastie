from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.user import User
from podcastie_telegram_html.tags import link

from bot.middlewares import DatabaseMiddleware
from bot.router.callback.menu import send_menu

router = Router()
router.message.middleware(DatabaseMiddleware(create_user=True))

@router.message(CommandStart())
async def handle_start_command(message: Message, state: FSMContext, user: User, bot: Bot) -> None:
    text = (
        f"👋 Hi there, {message.from_user.first_name}!\n"
        f"\n"
        f"I'm {link("Podcastie Bot", "https://t.me/podcastie_bot")}, "
        "and I'm here to help you stay updated with your favorite podcasts! 🎧\n"
        "\n"
        "To get started, simply grab the RSS feed URL of your favorite podcast and use the /follow command.\n"
        "\n"
        "Type /help to see all available commands."
    )

    await message.answer(text)
    await send_menu(bot, message.chat.id, user=user)
