from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    follow = State()
    unfollow = State()
