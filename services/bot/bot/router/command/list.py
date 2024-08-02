import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.podcast import Podcast
from podcastie_database.models.user import User
from podcastie_telegram_html.tags import link

from bot.filters import StatePresenceFilter
from bot.middlewares import DatabaseMiddleware

router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(Command("list"), StatePresenceFilter(has_state=False))
async def handle_list_command(message: Message, user: User) -> None:
    if not user.following_podcasts:
        await message.answer(
            "📭 You don't follow any podcasts yet! Start by using the /follow command."
        )
        return

    response = "List of podcasts you follow:\n"
    for object_id in user.following_podcasts:
        podcast = await Podcast.find_one(Podcast.id == object_id)

        status = "👌" if podcast.latest_episode_info.check_success else "⚠️"
        last_check_date = datetime.datetime.fromtimestamp(
            podcast.latest_episode_info.check_ts
        ).strftime("%d/%m/%Y %H:%M:%S")

        response += (
            f"{status} {link(podcast.meta.title, podcast.meta.link)} "
            f"(<code>{podcast.ppid}</code>) [{link("FEED", podcast.feed_url)}] "
            f"(last check {last_check_date} UTC)\n\n"
        )

    await message.answer(response, disable_web_page_preview=True)
