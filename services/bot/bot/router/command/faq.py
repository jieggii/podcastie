from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from podcastie_telegram_html.tags import bold, italic

from bot.filters import StatePresenceFilter

router = Router()


_QUESTIONS = {
    "What is RSS feed?": (
        "An RSS feed is a special link that lets you get the latest episodes and updates from a podcast automatically. "
        "Think of it as a subscription service that keeps you up-to-date with new content without having to check manually. "
        "Here is an example RSS feed URL to the Joe Rogan Experience podcast: https://feeds.megaphone.fm/GLT1412515089."
    ),
    "Where do I get my favorite podcast RSS feed URL?": (
        "You can usually find the RSS feed URL on the podcast’s official website. "
        "Look for an icon that looks like a small orange radio wave, often found at the bottom of the page or on a “Subscribe” section. "
        'If you have trouble, you can often ask the podcast host or search online for "[Podcast Name] RSS".'
    ),
    "What is PPID?": (
        "PPID (Podcastie Podcast ID) is a unique identifier of a podcast withing the Podcastie's database. "
        "This ID helps you manage and interact with podcasts easily."
    )
}

_MESSAGE = ""
for i, (q, a) in enumerate(_QUESTIONS.items()):
    _MESSAGE += (
        f"{bold(f"{i + 1}. {q}")}\n"
        f"{italic(a)}\n"
        "\n"
    )


@router.message(Command("faq"), StatePresenceFilter(has_state=False))
async def handle_faq(message: Message) -> None:
    await message.answer("Here are some useful questions and answers to them!")
    await message.answer(_MESSAGE, disable_web_page_preview=True)
