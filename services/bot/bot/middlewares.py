from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from podcastie_database.models import User

# async def db_user_middleware(
#     handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
#     message: Message,
#     data: dict[str, Any],
# ) -> Any:
#


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        print("called middleware")
        user = await User.find_one(User.user_id == event.from_user.id)
        if not user:
            user = User(user_id=event.from_user.id)
            await user.insert()
        data["user"] = user
        return await handler(event, data)
