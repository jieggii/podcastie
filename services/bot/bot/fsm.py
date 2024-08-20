from aiogram.fsm.state import State, StatesGroup

__all__ = ("BotState",)


class BotState(StatesGroup):
    FIND = State()
    IMPORT = State()
