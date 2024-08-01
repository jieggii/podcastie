from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from podcastie_telegram_html.tags import bold

router = Router()


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(
        f"{bold("Manage subscriptions")}\n"
        "/follow - start following podcast.\n"
        "/unfollow - stop following podcast.\n"
        "/list — list podcasts you are following.\n"
        "\n"
        f"{bold("Import and export subscriptions")}\n"
        "/import - import subscriptions from an OPML file.\n"
        "/export - export subscriptions as OPML file.\n"
        "\n"
        f"{bold("Get more info")}\n"
        "/faq — get list of frequently asked questions.\n"
        "/about — get additional information about the bot.\n"
        "/help — get this useful help message again.\n"
    )
