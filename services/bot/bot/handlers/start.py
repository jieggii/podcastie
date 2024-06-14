from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        f"👋 Hi there, {message.from_user.first_name}!\n"
        f"\n"
        "I'm <a href='https://t.me/podcastie_bot'>Podcastie Bot</a>, "
        "and I'm here to help you stay updated with your favorite podcasts! 🎧\n"
        "\n"
        "To get started, simply grab the RSS feed URL of your favorite podcast and use the /follow command.\n"
        "\n"
        "Type /help to see all available commands."
    )
