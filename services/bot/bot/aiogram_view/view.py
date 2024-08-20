import typing
from abc import ABC, abstractmethod

from aiogram.types import CallbackQuery, Message


class View(ABC):
    @abstractmethod
    async def handle_entrypoint(
        self, event: Message | CallbackQuery, data: dict[str, typing.Any]
    ) -> None:
        pass

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        raise NotImplementedError()
