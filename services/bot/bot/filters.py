from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


class StatePresenceFilter(Filter):
    def __init__(self, *, has_state: bool) -> None:
        self._has_state = has_state

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        state = await state.get_state()
        if bool(state) == self._has_state:
            return True
        return False
