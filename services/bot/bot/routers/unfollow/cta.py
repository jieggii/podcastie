from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot import util
from bot.callback_data.open_view import OpenImportView, OpenFindPodcastView

from bot.middlewares import DatabaseMiddleware
from bot.callback_data.unfollow import UnfollowCTACallbackData, UnfollowPromptCallbackData, ReturnTo
from bot.core.user import User


router = Router(name="cta")
router.message.middleware(DatabaseMiddleware(create_user=True))
router.callback_query.middleware(DatabaseMiddleware(create_user=True))


async def send_cta(bot: Bot, user: User, *, chat_id: int, edit_message_id: int | None = None):
    subscriptions = await user.get_following_podcasts()
    if not subscriptions:
        text = "You don't follow any podcast yet. Start by finding a podcast or importing your subscriptions!"

        kbd = InlineKeyboardBuilder()
        kbd.button(text="Find a podcast", callback_data=OpenFindPodcastView(edit_current_message=True))
        kbd.button(text="Import subscriptions", callback_data=OpenImportView(edit_current_message=True))
        markup = kbd.as_markup()

        if edit_message_id:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=edit_message_id, reply_markup=markup)
        else:
            await bot.send_message(chat_id, text, reply_markup=markup)

        return

    text = "Choose a podcasts to unfollow:"
    kbd = InlineKeyboardBuilder()
    for podcast in subscriptions:
        kbd.button(
            text=podcast.db_object.meta.title,
            callback_data=UnfollowPromptCallbackData(podcast_id=podcast.db_object.id, return_to=ReturnTo.UNFOLLOW_LIST)
        )
    kbd.adjust(2)
    markup = kbd.as_markup()

    # await util.se/nd_cta(bot, chat_id, text, edit_message_id=edit_message_id, answer_callback_query_id=None, reply_markup=markup)

@router.callback_query(UnfollowCTACallbackData.filter())
async def handle_cta_callback_query(query: CallbackQuery, bot: Bot, user: User):
    await send_cta(bot, user, chat_id=query.message.chat.id, edit_message_id=query.message.message_id)


@router.message(Command("unfollow"))
async def handle_cta_command(message: Message, bot: Bot, user: User) -> None:
    await send_cta(bot, user, chat_id=message.chat.id)
