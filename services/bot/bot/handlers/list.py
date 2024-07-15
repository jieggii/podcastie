import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models import Podcast, User
from podcastie_telegram_html import link

from bot.middlewares import DatabaseMiddleware

router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(Command("list"))
async def handle_list_command(message: Message, state: FSMContext, user: User) -> None:
    if not user.following_podcasts:
        await message.answer(
            "📭 You don't follow any podcasts yet! Start by using the /follow command."
        )
        return

    response = "List of podcasts you follow:\n"
    for object_id in user.following_podcasts:
        podcast = await Podcast.find_one(Podcast.id == object_id)
        fmt_status = "✅" if podcast.latest_episode_check_successful else "❌"
        fmt_last_check_date = datetime.datetime.fromtimestamp(
            podcast.latest_episode_checked
        ).strftime("%H:%M:%S %D.%M.%Y")
        response += (
            f"• {link(podcast.title, podcast.link)} "
            f"<code>{podcast.ppid}</code> "
            f"(last check: {fmt_last_check_date}, status: {fmt_status})\n\n"
        )

    await message.answer(response, disable_web_page_preview=True)
