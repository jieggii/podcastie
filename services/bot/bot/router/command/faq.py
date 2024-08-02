from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.filters import StatePresenceFilter

router = Router()


@router.message(Command("faq"), StatePresenceFilter(has_state=False))
async def handle_faq(message: Message) -> None:
    await message.answer("Here are some useful questions and answers to them!")
    await message.answer(
        "<b>1. What is RSS feed and where do I get a URL for it?</b>\n"
        "<i>For podcasts, an RSS feed contains the latest episodes and information about the show."
        "You can usually find the RSS feed URL on the podcast's website. "
        "Look for the RSS icon, typically orange and white, often found in the footer or on the subscription page.</i>\n"
        "\n"
        "<b>2. What is PPID?</b>\n"
        "<i>PPID (Podcastie Podcast ID) is a unique identifier of a podcast within the Podcastie's database. "
        "This ID helps you manage and interact with podcasts easily.</i>"
    )
