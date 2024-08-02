from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from podcastie_database.models.podcast import Podcast
from podcastie_database.models.user import User

from bot.core.opml import generate_opml
from bot.middlewares import DatabaseMiddleware
from bot.filters import StatePresenceFilter


router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(Command("export"), StatePresenceFilter(has_state=False))
async def handle_export_command(message: Message, user: User, bot: Bot) -> None:
    if not user.following_podcasts:
        await message.answer("You have nothing to export yet!")
        return

    podcasts = [
        await Podcast.find_one(Podcast.id == podcast_id)
        for podcast_id in user.following_podcasts
    ]
    opml = generate_opml(podcasts)
    file = BufferedInputFile(opml.encode(), "Podcastie.opml.xml")

    await message.answer("📄 Here are your subscriptions in opml format:")
    await bot.send_chat_action(message.from_user.id, ChatAction.UPLOAD_DOCUMENT)
    await message.answer_document(file)
