from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callback_data.open_view import OpenFindPodcastView
from bot.core.podcast import Podcast, PodcastNotFoundError

from bot.middlewares import DatabaseMiddleware
from bot.core.user import User, UserDoesNotFollowPodcastError
from podcastie_telegram_html.tags import bold
from bot.callback_data.unfollow import UnfollowCTACallbackData, UnfollowCallbackData, UnfollowPromptCallbackData, ReturnTo
from bot.callback_data.subscriptions import SubscriptionsCTACallbackData as SubscriptionsListCallbackData

def _match_return_to(return_to: ReturnTo) -> UnfollowCTACallbackData | SubscriptionsListCallbackData:
    match return_to:
        case ReturnTo.UNFOLLOW_LIST:
            return UnfollowCTACallbackData()
        case ReturnTo.SUBSCRIPTIONS_LIST:
            return SubscriptionsListCallbackData(edit_current_message=True)
        case _:
            raise ValueError(f"unexpected return_to value: {return_to}")


router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())

@router.callback_query(UnfollowCallbackData.filter())
async def handle_unfollow_view(query: CallbackQuery, bot: Bot, user: User, callback_data: UnfollowCallbackData):
    try:
        podcast = await Podcast.from_object_id(callback_data.podcast_id)
    except PodcastNotFoundError:
        await query.message.answer("Error: podcast not found")  # todo: better error handling
        return

    try:
        await user.unfollow_podcast(podcast)
    except UserDoesNotFollowPodcastError:
        await query.message.answer("Error: you do not follow this podcast.")  # todo: better error handling
        return

    kbd = InlineKeyboardBuilder()
    kbd.button(text="« Back", callback_data=_match_return_to(callback_data.return_to))
    markup = kbd.as_markup()

    await query.answer(f"You have successfully unsubscribed from {bold(podcast.db_object.meta.title)}")
    await query.message.edit_text(f"You have successfully unsubscribed from {podcast.db_object.meta.title}", reply_markup=markup)

@router.callback_query(UnfollowPromptCallbackData.filter())
async def handle_confirmation_view(query: CallbackQuery, bot: Bot, user: User, callback_data: UnfollowPromptCallbackData):
    try:
        podcast = await Podcast.from_object_id(callback_data.podcast_id)
    except PodcastNotFoundError:
        await query.message.answer("Error: podcast not found")  # todo: better error handling
        return

    kbd = InlineKeyboardBuilder()
    kbd.button(text="Yes", callback_data=UnfollowCallbackData(podcast_id=podcast.db_object.id, return_to=callback_data.return_to))
    kbd.button(text="Cancel", callback_data=_match_return_to(callback_data.return_to))

    markup = kbd.as_markup()

    await query.message.edit_text(f"Are you sure you want to unfollow {bold(podcast.db_object.meta.title)}?", reply_markup=markup)


