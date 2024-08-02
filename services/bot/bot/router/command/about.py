from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.filters import StatePresenceFilter



router = Router()


@router.message(Command("about"), StatePresenceFilter(has_state=False))
async def handle_about(message: Message) -> None:
    await message.answer("This is a stub about message.")
