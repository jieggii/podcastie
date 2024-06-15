from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# from bot.middlewares import DatabaseMiddleware

router = Router()
# router.message.middleware(DatabaseMiddleware())


@router.message(Command("search"))
async def handle_follow_command(
    message: Message,
    state: FSMContext,
) -> None:
    await message.answer("This command is not yet implemented.")
