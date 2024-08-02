from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import InlineQuery, Message
from podcastie_database.models.user import User

_HANDLER_TYPE = Callable[[Message | InlineQuery, Dict[str, Any]], Awaitable[Any]]
_EVENT_TYPE = Message | InlineQuery
_DATA_TYPE = Dict[str, Any]

class DatabaseMiddleware(BaseMiddleware):
    _create_user: bool

    def __init__(self, create_user: bool = True) -> None:
        self._create_user = create_user

    async def __call__(self, handler: _HANDLER_TYPE, event: _EVENT_TYPE, data: _DATA_TYPE) -> Any:
        user = await User.find_one(User.user_id == event.from_user.id)
        if not user and self._create_user:
            user = User(user_id=event.from_user.id)
            await user.insert()
        data["user"] = user
        return await handler(event, data)
