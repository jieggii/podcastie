from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import InlineQuery, Message

from bot.core.user import User, UserNotFoundError

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
        db_object = await UserDBModel.find_one(
            UserDBModel.user_id == event.from_user.id
        )
        if not db_object and self._create_user:
            db_object = UserDBModel(user_id=event.from_user.id)
            await db_object.insert()

        data["user"] = User(db_object)
        return await handler(event, data)
