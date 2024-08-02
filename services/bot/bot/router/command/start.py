import base64
import binascii

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.user import User
from podcastie_telegram_html import tags

from bot.core import subscription_manager
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_ppid

router = Router()
router.message.middleware(DatabaseMiddleware(create_user=False))


def parse_ppid_param(message_text: str) -> str | None:
    tokens = message_text.split(maxsplit=2)
    if len(tokens) != 2:
        return None

    ppid_encoded = tokens[1]
    return base64.urlsafe_b64decode(ppid_encoded.encode()).decode()

def format_failed_transaction_identifier(
    t: subscription_manager.TransactionResultFailure,
) -> str:
    if t.podcast_title:
        return tags.link(t.podcast_title, t.podcast_link)
    return tags.code(t.action.target_identifier.value)


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, user: User) -> None:
    # reset user's state to restart the bot:
    await state.clear()

    # parse bot deeplink param (https://core.telegram.org/api/links#bot-links):
    ppid: str | None = None
    try:
        ppid = parse_ppid_param(message.text)
    except binascii.Error:
        await message.answer("⚠️ Failed to decode PPID provided as a parameter.")

    if (not user) or (user and not ppid):
        await message.answer(
            f"👋 Hi there, {message.from_user.first_name}!\n"
            f"\n"
            "I'm <a href='https://t.me/podcastie_bot'>Podcastie Bot</a>, "
            "and I'm here to help you stay updated with your favorite podcasts! 🎧\n"
            "\n"
            "To get started, simply grab the RSS feed URL of your favorite podcast and use the /follow command.\n"
            "\n"
            "Type /help to see all available commands.",
        )

    if not ppid:
        return

    if not is_ppid(ppid):
        await message.answer("⚠️ PPID provided as a parameter is not valid.")
        return

    if not user:
        user = User(
            user_id=message.from_user.id
        )  # todo: implement User.from_user_id(...)
        await user.insert()

    manager = subscription_manager.SubscriptionsManager(user)
    await manager.follow_by_ppid(ppid)
    succeeded, failed = await manager.commit()

    response: str
    if succeeded:
        transaction = succeeded[0]
        response = (
            f"✨ You have successfully subscribed to {tags.link(transaction.podcast_title, transaction.podcast_link)}\n"
            f"From now on, you will receive new episodes of this podcast as soon as they are released!\n\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow podcasts."
        )
    else:
        transaction = failed[0]
        response = f"⚠️ Failed to subscribe to {format_failed_transaction_identifier(transaction)}: {transaction.error_message}."

    await message.answer(response, disable_web_page_preview=len(succeeded) == 0)
