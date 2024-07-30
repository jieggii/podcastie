import io

from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.user import User
from podcastie_telegram_html.tags import link
from structlog import get_logger

from bot.core import opml, subscription_manager
from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_feed_url

log = get_logger()
router = Router()
router.message.middleware(DatabaseMiddleware())

MAX_SUBSCRIPTIONS = 20
MAX_FILE_SIZE = 1370 * 10  # todo
SUPPORTED_MIME_TYPES = ("application/xml",)


def format_failed_transaction_identifier(
    t: subscription_manager.TransactionResultFailure,
) -> str:
    if t.podcast_title:
        return link(t.podcast_title, t.podcast_link)
    return t.action.target_identifier.value


@router.message(States.IMPORT)
async def handle_import_state(
    message: Message, state: FSMContext, user: User, bot: Bot
) -> None:
    global log
    if not message.document:
        await message.answer(
            "⚠  It seems that what you sent is not a file! Please attach an OPML XML file or /cancel this action."
        )
        return

    if message.document.file_size > MAX_FILE_SIZE:
        await message.answer(
            "⚠  Sorry, but file size is too big to process it. Please try another file or /cancel this action."
        )
        return

    if message.document.mime_type not in SUPPORTED_MIME_TYPES:
        await message.answer(
            "⚠  The file you sent has incorrect file mime type and will not be processed. Please try another file or /cancel this action."
        )
        return

    await bot.send_chat_action(message.from_user.id, ChatAction.TYPING)

    file = await bot.get_file(message.document.file_id)

    file_content = io.BytesIO()
    await bot.download_file(file.file_path, file_content)

    try:
        feed_urls = opml.parse_opml(file_content.read())
    except opml.OPMLParseError:
        await message.answer(
            "⚠  I failed to parse this OPML file. Please try another file or /cancel this action."
        )
        return

    if not feed_urls:
        await message.answer(
            "⚠  The OPML file does not contain any subscriptions. Please try another file or /cancel this action."
        )
        return

    # start follow transaction:
    manager = subscription_manager.SubscriptionsManager(user)
    invalid_urls: list[str] = []
    for url in feed_urls:
        if not is_feed_url(url):
            invalid_urls.append(url)
            continue
        await manager.follow_by_feed_url(url)

    succeeded, failed = await manager.commit()

    response: str
    if succeeded:  # if followed all podcasts without any fails
        response = "✨ You have successfully subscribed to the following podcasts:\n"
        for transaction in succeeded:
            response += (
                f"👌 {link(transaction.podcast_title, transaction.podcast_link)}\n"
            )

        response += (
            "\n"
            "From now on, you will receive new episodes of these podcasts as soon as they are released!\n"
            "\n"
        )

        for url in invalid_urls:
            response += f"⚠  {url}: does not look like a valid URL\n"

        for transaction in failed:
            response += f"⚠  {format_failed_transaction_identifier(transaction)}: {transaction.error_message}\n"

        response += (
            "\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow from podcasts."
        )

        await state.clear()

    else:  # if did not follow any podcasts, all were failed
        response = "❌ Failed to subscribe to any of the provided podcasts.\n\n"
        for url in invalid_urls:
            response += f"⚠  {url}: does not look like a valid URL\n"

        for transaction in failed:
            response += f"⚠  {format_failed_transaction_identifier(transaction)}: {transaction.error_message}\n"

        response += "\n" "Please try again or /cancel this action."

    await message.answer(response, disable_web_page_preview=len(succeeded) != 1)


@router.message(Command("import"))
async def handle_import_command(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(States.IMPORT)
    await message.answer(
        f"🚢️ Please send me an OPML XML file to import your subscriptions.\n"
        "\n"
        "You can /cancel this action.",
    )
