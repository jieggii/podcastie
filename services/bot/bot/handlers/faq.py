from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("faq"))
async def handle_faq(message: Message) -> None:
    await message.answer("Catch are some useful questions and their answers!")
    await message.answer(
        "<b>1. What is RSS feed and where do I get a URL for it?</b>\n"
        "<i>For podcasts, an RSS feed contains the latest episodes and information about the show."
        "You can usually find the RSS feed URL on the podcast's website, "
        "or you can search for it on your favorite podcast directory like Apple Podcasts, Spotify, or Google Podcasts. "
        'Look for a button or link that says "RSS" or "Subscribe".</i>\n'
        "\n"
        "<b>2. What is PPID</b>\n"
        "<i>PPID (Podcastie Podcast ID) is a unique identifier of a podcast within the bot's database. "
        "This ID helps you manage and interact with your followed podcasts easily.</i>"
    )
