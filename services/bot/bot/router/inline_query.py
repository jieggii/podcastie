from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import hashlib

from podcastie_database import User

from bot.middlewares import DatabaseMiddleware

router = Router()

router.inline_query.middleware(DatabaseMiddleware(create_user=False))


@router.inline_query()
async def handle_inline_query(query: InlineQuery, user: User | None) -> None:
    if user:
        text = str(user.user_id)
    else:
        text = "unknown user"

    input_content = InputTextMessageContent(message_text=text)
    result_id: str = hashlib.md5(text.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=f'Result {text}',
        input_message_content=input_content,
    )

    await query.answer(
        results=[
            item
        ],
        cache_time=1
    )
