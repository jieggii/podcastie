import aiogram
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
)
from beanie.operators import Text
from podcastie_database.models.podcast import Podcast
from podcastie_database.models.user import User
from podcastie_telegram_html import tags, util, components

from bot.middlewares import DatabaseMiddleware

router = Router()

router.inline_query.middleware(DatabaseMiddleware(create_user=False))


@router.inline_query()
async def handle_inline_query(query: InlineQuery, user: User | None, bot: aiogram.Bot) -> None:
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
        follow_link = components.start_bot_link(
            "📬 click to follow",
            bot_username=(await bot.me()).username,
            payload=podcast.ppid,
            encode_payload=True,
        )
        description = util.escape(podcast.meta.description) if podcast.meta.description else ""
        description_len = len(description)

        message_text = (
            f"{tags.bold(podcast.meta.title)} ({follow_link})\n"
            f"{tags.blockquote(description, expandable=description_len > 800)}"  # todo: const magic number
        )

        message_content = InputTextMessageContent(
            message_text=message_text,
            link_preview_options=LinkPreviewOptions(
                url=podcast.meta.link, prefer_small_media=description_len != 0
            )
        )

        articles.append(
            InlineQueryResultArticle(
                id=podcast.meta.hash(),
                title=podcast.meta.title,
                input_message_content=message_content,
                url=podcast.meta.link,
                description=podcast.meta.description,
                thumbnail_url=podcast.meta.cover_url,
            )
        )

    await query.answer(
        results=articles,
        cache_time=1,
        is_personal=result_is_personal,
    )
