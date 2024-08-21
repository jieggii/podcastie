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
from beanie import PydanticObjectId
from podcastie_telegram_html import components, tags, util

from bot.core.podcast import Podcast, search_podcasts
from bot.core.user import User
from bot.middlewares import DatabaseMiddleware

router = Router()
router.inline_query.middleware(DatabaseMiddleware(create_user=False))


def _build_reply_markup(
    bot_username: str, podcast_id: PydanticObjectId, podcast_link: str | None
) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    if podcast_link:
        kbd.button(text="Website", url=podcast_link)

    kbd.button(
        text="Follow via @podcastie_bot",
        url=components.start_bot_url(
            bot_username=bot_username,
            payload=str(podcast_id),
            encode_payload=True,
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
        subscriptions = await user.get_following_podcasts()

    if subscriptions:
        result_is_personal = True

        if query_text:
            # display search results. search results within podcasts user follow are shown first
            all_results = await search_podcasts(query_text)

            prioritized = []
            other = []

            for podcast in all_results:
                if user.is_following_podcast(podcast):
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
            util.escape(podcast.db_object.meta.description)
            if podcast.db_object.meta.description
            else ""
        )
        description_len = len(description)

        message_text = (
            f"{tags.bold(podcast.db_object.meta.title)}\n"
            f"{tags.blockquote(description, expandable=description_len > 800)}"  # todo: const magic number
        )

        message_content = InputTextMessageContent(
            message_text=message_text,
            link_preview_options=LinkPreviewOptions(
                url=podcast.db_object.meta.link, prefer_small_media=description_len != 0
            ),
        )

        articles.append(
            InlineQueryResultArticle(
                id=podcast.db_object.meta.hash(),
                title=podcast.db_object.meta.title,
                input_message_content=message_content,
                url=podcast.db_object.meta.link,
                description=podcast.db_object.meta.description,
                thumbnail_url=podcast.db_object.meta.cover_url,
                reply_markup=_build_reply_markup(
                    bot_username=(await bot.get_me()).username,
                    podcast_id=podcast.db_object.id,
                    podcast_link=podcast.db_object.meta.link,
                ),
            )
        )

    await query.answer(
        results=articles,
        cache_time=1,
        is_personal=result_is_personal,
    )
