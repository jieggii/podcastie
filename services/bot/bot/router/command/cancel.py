from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters import StatePresenceFilter

router = Router()


@router.message(Command("cancel"), StatePresenceFilter(has_state=True))
@router.message(F.default_text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("The action was cancelled.")
