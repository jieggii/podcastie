from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import hashlib
from beanie.operators import Text

from podcastie_database import User, Podcast

from bot.middlewares import DatabaseMiddleware

router = Router()

router.inline_query.middleware(DatabaseMiddleware(create_user=False))


@router.inline_query()
async def handle_inline_query(query: InlineQuery, user: User | None) -> None:
    query_text = query.query
    # query_text_hash = hashlib.md5(query_text.encode()).hexdigest()

    podcasts = await Podcast.find(Text(query_text)).to_list()
    inline_results: list[InlineQueryResultArticle] = []
    for podcast in podcasts:
        input_message_content = InputTextMessageContent(message_text=podcast.link if podcast.link else podcast.ppid)  # todo
        inline_results.append(InlineQueryResultArticle(
            id=podcast.ppid,
            title=podcast.title,
            input_message_content=input_message_content,
            description=podcast.description,
            thumbnail_url=podcast.cover_url
        ))

    await query.answer(
        results=inline_results,
        cache_time=1
    )
