import aiogram
from aiogram import Router
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_telegram_html import tags, util

from bot.utils.instant_link import build_instant_link
from podcastie_core.podcast import Podcast
from podcastie_core.service import search_podcasts, user_subscriptions, user_is_following_podcast
from podcastie_core.user import User
from bot.middlewares import UserMiddleware

router = Router()
router.inline_query.middleware(UserMiddleware(create_user=False))


def _build_reply_markup(
    bot_username: str, podcast_feed_url_hash_prefix: str, podcast_link: str | None
) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    if podcast_link:
        kbd.button(text="Website", url=podcast_link)

    kbd.button(
        text="Follow via Podcastie Bot",
        url=build_instant_link(
            bot_username=bot_username,
            podcast_feed_url_hash_prefix=str(podcast_feed_url_hash_prefix),
        ),
    )

    return kbd.as_markup()


@router.inline_query()
async def handle_inline_query(
    query: InlineQuery, bot: aiogram.Bot, user: User | None
) -> None:
    query_text = query.query

    results: list[Podcast]  # search results that will be displayed to user
    result_is_personal: bool

    subscriptions: list[Podcast] | None = None
    if user:
        subscriptions = await user_subscriptions(user)

    if subscriptions:
        result_is_personal = True

        if query_text:
            # display search results. search results within podcasts user follow are shown first
            all_results = await search_podcasts(query_text)

            prioritized = []
            other = []

            for podcast in all_results:
                if user_is_following_podcast(user, podcast):
                    prioritized.append(podcast)
                else:
                    other.append(podcast)

            results = prioritized + other

        else:
            # display user's subscriptions
            results = subscriptions

    else:
        result_is_personal = False

        if query_text:
            # display search results among all podcasts
            results = await search_podcasts(query_text)
        else:
            # do not display anything
            results = []

    articles: list[InlineQueryResultArticle] = []
    for podcast in results:
        description = (
            util.escape(podcast.document.meta.description)
            if podcast.document.meta.description
            else ""
        )
        description_len = len(description)

        message_text = (
            f"{tags.bold(podcast.document.meta.title)}\n"
            f"{tags.blockquote(description, expandable=description_len > 800)}"  # todo: const magic number
        )

        message_content = InputTextMessageContent(
            message_text=message_text,
            link_preview_options=LinkPreviewOptions(
                url=podcast.document.meta.link, prefer_small_media=description_len != 0
            ),
        )

        articles.append(
            InlineQueryResultArticle(
                id=podcast.document.meta.hash(),
                title=podcast.document.meta.title,
                input_message_content=message_content,
                url=podcast.document.meta.link,
                description=podcast.document.meta.description,
                thumbnail_url=podcast.document.meta.cover_url,
                reply_markup=_build_reply_markup(
                    bot_username=(await bot.get_me()).username,
                    podcast_feed_url_hash_prefix=podcast.document.feed_url_hash_prefix,
                    podcast_link=podcast.document.meta.link,
                ),
            )
        )

    await query.answer(
        results=articles,
        cache_time=1,
        is_personal=result_is_personal,
    )
