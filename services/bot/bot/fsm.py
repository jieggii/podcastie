from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


__all__ = ("BotState",)

class BotState(StatesGroup):
    FIND = State()
    IMPORT = State()
