from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from podcastie_database.models import User, Podcast

router = Router()


@router.message(Command("export"))
async def handle_about(message: Message, user: User) -> None:
    if not user.following_podcasts:
        await message.answer("You have nothing to export yet!")
        return

    podcasts = [
        await Podcast.find_one(Podcast.id == podcast_id)
        for podcast_id in user.following_podcasts
    ]
