from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie.odm.fields import PydanticObjectId

from bot.callback_data.follow import FollowCallbackData
from bot.callback_data.unfollow import UnfollowCallbackData
from bot.core.podcast import Podcast, PodcastNotFoundError
from bot.core.user import User, UserFollowsPodcastError
from bot.middlewares import DatabaseMiddleware

router = Router()
router.callback_query.middleware(DatabaseMiddleware(create_user=True))


def _build_unfollow_podcast_reply_markup(
    podcast_id: PydanticObjectId, podcast_link: str
) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="Unfollow", callback_data=UnfollowCallbackData(podcast_id=podcast_id)
    )
    kbd.button(text="Podcast website", url=podcast_link)

    return kbd.as_markup()


@router.callback_query(FollowCallbackData.filter())
async def handle_follow_query(
    query: CallbackQuery, user: User, callback_data: FollowCallbackData
):
    try:
        podcast = await Podcast.from_object_id(callback_data.podcast_id)
    except PodcastNotFoundError:
        await query.answer(
            f"🚫 This podcast no longer exist in my database", show_alert=True
        )
        return

    try:
        await user.follow_podcast(podcast)
    except UserFollowsPodcastError:
        await query.answer(
            f"🚫 You already follow {podcast.db_object.meta.title}", show_alert=True
        )
        return

    markup = _build_unfollow_podcast_reply_markup(
        podcast.db_object.id, podcast.db_object.meta.link
    )
    await query.message.edit_reply_markup(reply_markup=markup)

    await query.answer(f"👌 Successfully followed {podcast.db_object.meta.title}")
