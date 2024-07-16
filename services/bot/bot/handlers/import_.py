import time

import aiohttp
import podcastie_rss
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database import Podcast, User
from structlog import get_logger

from podcastie_telegram_html import link

from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.ppid import generate_ppid
from bot.validators import is_feed_url, is_ppid

log = get_logger()
router = Router()
router.message.middleware(DatabaseMiddleware())


MAX_SUBSCRIPTIONS = 20


@router.message(States.IMPORT)
async def handle_import_state(
    message: Message, state: FSMContext, user: User, bot: Bot
) -> None:
    global log
    await message.answer("This command is not yet implemented. 🚢🚢🚢")

@router.message(Command("import"))
async def handle_import_command(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(States.IMPORT)
    await message.answer(
        f"🚢️ Please send me an OPML file from which you want to import your subscriptions.\n"
        "\n"
        "You can /cancel this action.",
    )
