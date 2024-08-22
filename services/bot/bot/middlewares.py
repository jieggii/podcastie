from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import InlineQuery, Message

from podcastie_core.user import User, UserNotFoundError

_HANDLER_TYPE = Callable[[Message | InlineQuery, Dict[str, Any]], Awaitable[Any]]
_EVENT_TYPE = Message | InlineQuery
_DATA_TYPE = Dict[str, Any]


class UserMiddleware(BaseMiddleware):
    _create_user: bool

    def __init__(self, create_user: bool = True) -> None:
        self._create_user = create_user

    async def __call__(
        self, handler: _HANDLER_TYPE, event: _EVENT_TYPE, data: _DATA_TYPE
    ) -> Any:
        user_id = event.from_user.id

        user: User | None = None
        try:
            user = await User.from_user_id(user_id)
        except UserNotFoundError:
            if self._create_user:
                user = await User.new_from_user_id(user_id)

        data["user"] = user

        return await handler(event, data)
