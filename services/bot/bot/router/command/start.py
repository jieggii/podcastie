import base64

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from podcastie_database import User
from podcastie_telegram_html import tags
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_ppid
from bot.core.follow_transaction import FollowTransaction

router = Router()
router.message.middleware(DatabaseMiddleware(create_user=False))

@router.message(CommandStart())
async def handle_start(message: Message, user: User) -> None:
    tokens = message.text.split(maxsplit=2)
    ppid: str | None = None
    if len(tokens) == 2:
        ppid_encoded = tokens[1]
        ppid = base64.urlsafe_b64decode(ppid_encoded.encode()).decode()

    if not user or (user and not ppid):
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
        await message.answer("⚠️ PPID provided as an argument is not valid.")
        return

    if not user:
        user = User(user_id=message.from_user.id)  # todo: implement User.from_user_id(...)
        await user.insert()

    transaction = FollowTransaction(user)
    await transaction.follow_podcast_by_ppid(ppid)
    result = await transaction.commit()

    text: str
    if result.succeeded:
        item = result.succeeded[0]
        text = (
            f"✨ You have successfully subscribed to {tags.link(item.podcast_title, item.podcast_link)}\n"
            f"From now on, you will receive new episodes of this podcast as soon as they are released!\n\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow podcasts."
        )
    else:
        item = result.failed[0]
        text = f"⚠️Failed to subscribe to {tags.link(item.podcast_title, item.podcast_link)}: {item.message}."

    await message.answer(text, disable_web_page_preview=len(result.succeeded) == 0)
