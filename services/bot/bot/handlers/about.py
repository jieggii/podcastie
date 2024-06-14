from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("about"))
async def handle_about(message: Message) -> None:
    await message.answer("stub about message")
