from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.user import User
from podcastie_telegram_html.tags import code, link
from structlog import get_logger

from bot.core import subscription_manager
from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_feed_url, is_ppid

log = get_logger()
router = Router()
router.message.middleware(DatabaseMiddleware())

MAX_IDENTIFIERS = 20


def format_failed_transaction_identifier(t: subscription_manager.TransactionResultFailure) -> str:
    if t.podcast_title:
        return link(t.podcast_title, t.podcast_link)

    if t.action.target_identifier.type == subscription_manager.PodcastIdentifierType.PPID:
        return code(t.action.target_identifier.value)

    return t.action.target_identifier.value


@router.message(States.FOLLOW)
async def handle_follow_state(
    message: Message, state: FSMContext, user: User, bot: Bot
) -> None:
    global log

    identifiers = message.text.split("\n", maxsplit=MAX_IDENTIFIERS)

    if len(identifiers) > MAX_IDENTIFIERS:
        await message.answer(f"⚠ {MAX_IDENTIFIERS} is the limit TODO")
        return

    # remove duplicated identifiers:
    identifiers = list(set(identifiers))

    # send TYPING type actions because response might take longer than usual:
    await bot.send_chat_action(user.user_id, ChatAction.TYPING)

    # create follow transaction:
    manager = subscription_manager.SubscriptionsManager(user)
    invalid_identifiers: list[str] = (
        []
    )  # list of identifiers that did not pass validation

    for identifier in identifiers:
        if is_ppid(identifier):
            await manager.follow_by_ppid(identifier)
        elif is_feed_url(identifier):
            await manager.follow_by_feed_url(identifier)
        else:
            invalid_identifiers.append(identifier)
            continue

    succeeded, failed = await manager.commit()

    response: str
    if succeeded:
        response = "✨ You have successfully subscribed to the following podcasts:\n"
        for transaction in succeeded:
            response += f"👌 {link(transaction.podcast_title, transaction.podcast_link)}\n"

        response += (
            "\n"
            "From now on, you will receive new episodes of these podcasts as soon as they are released!\n"
            "\n"
        )

        for identifier in invalid_identifiers:
            response += (
                f"⚠ ️{identifier}: identifier does not look like a valid URL or PPID\n"
            )

        for transaction in failed:
            response += f"⚠  {format_failed_transaction_identifier(transaction)}: {transaction.error_message}\n"

        response += (
            "\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow podcasts."
        )

        await state.clear()

    else:
        response = "❌ Failed to subscribe to any of the provided podcasts.\n\n"
        for identifier in invalid_identifiers:
            response += (
                f"⚠ ️{identifier}: identifier does not look like a valid URL or PPID\n"
            )

        for transaction in failed:
            response += f"⚠ ️{format_failed_transaction_identifier(transaction)}: {transaction.error_message}\n"

        response += "\n" "Please try again or /cancel this action."

    await message.answer(response, disable_web_page_preview=len(succeeded) != 1)


@router.message(Command("follow"))
async def handle_follow_command(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(States.FOLLOW)
    await message.answer(
        "🎙️ Please send me up to 20 RSS feed URLs or PPIDs.\n"
        "\n"
        "You can /cancel this action.",
    )
