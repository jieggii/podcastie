from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    FOLLOW = State()
    UNFOLLOW = State()