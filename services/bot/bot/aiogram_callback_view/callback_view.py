from abc import ABC, abstractmethod
import typing
from aiogram.types import CallbackQuery, Message


class CallbackView(ABC):
    @abstractmethod
    async def handle_entrypoint(self, event: Message | CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        pass

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        raise NotImplementedError()
