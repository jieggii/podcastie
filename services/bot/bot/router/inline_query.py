from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import hashlib
from beanie.operators import Text

from podcastie_database import User, Podcast
from podcastie_telegram_html import link, bold, optional, footer

from bot.middlewares import DatabaseMiddleware

router = Router()

router.inline_query.middleware(DatabaseMiddleware(create_user=False))


@router.inline_query()
async def handle_inline_query(query: InlineQuery, user: User | None) -> None:
    query_text = query.query

    podcasts: list[Podcast]
    result_is_personal: bool
    if query_text:
        result_is_personal = False
        podcasts = await Podcast.find(Text(query_text)).to_list()
    else:
        if user and user.following_podcasts:
            result_is_personal = True
            podcasts = [
                await Podcast.find_one(Podcast.id == podcast_id)
                for podcast_id in user.following_podcasts
            ]
        else:
            result_is_personal = True
            podcasts = []

    for podcast in podcasts: podcast.description = "Description is not available yet."

    articles: list[InlineQueryResultArticle] = []
    for podcast in podcasts:
        footer_items: list[str] = []
        if podcast.link:
            footer_items.append(link("podcast website", podcast.link))
        footer_items.append(link("subscribe", f"https://t.me/podcastie_bot?start={podcast.ppid}"))

        text = (
            f"{bold(podcast.title)}\n\n"
            f"{optional(podcast.description)}\n\n"
            f"{footer(footer_items)}"
        )
        message_content = InputTextMessageContent(
            message_text=text, parse_mode=ParseMode.HTML  # todo remove html
        )

        articles.append(InlineQueryResultArticle(
            id=podcast.ppid,
            title=podcast.title,
            input_message_content=message_content,
            description=podcast.description,
            thumbnail_url=podcast.cover_url
        ))

    await query.answer(
        results=articles,
        cache_time=1,
        is_personal=result_is_personal,
    )
