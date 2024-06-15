from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(
        "Here is the list of my commands:\n"
        "• /follow - start following podcast.\n"
        "• /unfollow - stop following podcast.\n"
        "• /list — list podcasts you are following.\n"
        "• /search - search for podcasts available in my database.\n"
        "\n"
        "• /faq — get list of frequently asked questions.\n"
        "• /about — get additional information about the bot.\n"
        "• /help — get this useful help message again.\n"
    )
