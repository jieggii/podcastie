import base64

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
)
from beanie.operators import Text
from podcastie_database import Podcast, User
from podcastie_telegram_html import tags, util

from bot.middlewares import DatabaseMiddleware

router = Router()

router.inline_query.middleware(DatabaseMiddleware(create_user=False))


@router.inline_query()
async def handle_inline_query(query: InlineQuery, user: User | None) -> None:
    query_text = query.query

    results: list[Podcast]  # search results that will be displayed to user

    result_is_personal: bool
    if user and user.following_podcasts:
        result_is_personal = True

        if not query_text:
            # display podcasts user follow
            results = [
                await Podcast.get(podcast_id) for podcast_id in user.following_podcasts
            ]
        else:
            # display search results. search results within
            # podcasts user follow are shown first
            all_results = await Podcast.find(Text(query_text)).to_list()
            prioritized = []
            other = []
            for podcast in all_results:
                if podcast.id in user.following_podcasts:
                    prioritized.append(podcast)
                else:
                    other.append(podcast)
            results = prioritized + other
    else:
        result_is_personal = False

        if not query_text:
            # do not display anything
            results = []
        else:
            # display search results among all podcasts
            results = await Podcast.find(Text(query_text)).to_list()

    articles: list[InlineQueryResultArticle] = []
    for podcast in results:
        escaped_description: str | None = (
            util.escape(podcast.description) if podcast.description else ""
        )

        ppid_encoded: str = base64.urlsafe_b64encode(podcast.ppid.encode()).decode()
        text = (
            f"{tags.bold(podcast.title)} ({tags.link("📬 click to subscribe", f"https://t.me/podcastie_bot?start={ppid_encoded}")})\n"
            f"<blockquote expandable>{escaped_description}</blockquote>"
        )
        message_content = InputTextMessageContent(
            message_text=text,
            link_preview_options=LinkPreviewOptions(
                url=podcast.link,
                prefer_small_media=True
            )
        )

        articles.append(
            InlineQueryResultArticle(
                id=podcast.ppid,
                title=podcast.title,
                input_message_content=message_content,
                url=podcast.link,
                description=podcast.description,
                thumbnail_url=podcast.cover_url,
            )
        )

    await query.answer(
        results=articles,
        cache_time=1,
        is_personal=result_is_personal,
    )
