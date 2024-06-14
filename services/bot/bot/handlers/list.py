from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models import Podcast, User

from bot.middlewares import DatabaseMiddleware

router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(Command("list"))
async def cancel_handler(message: Message, state: FSMContext, user: User) -> None:
    if not user.following_podcasts:
        await message.answer(
            "📭 You don't follow any podcasts yet! Start by using the /follow command."
        )
        return

    response = "List of podcasts you follow:\n"
    for object_id in user.following_podcasts:
        podcast = await Podcast.find_one(Podcast.id == object_id)
        latest_episode_date_str = (
            podcast.latest_episode_date.strftime("%d.%m.%Y")
            if podcast.latest_episode_date
            else "n/a"
        )
        response += f"• <a href='{podcast.link}'>{podcast.title}</a> (<code>{podcast.ppid}</code>), latest episode: {latest_episode_date_str}\n"

    await message.answer(response, disable_web_page_preview=True)
