from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database import Podcast, User
from podcastie_telegram_html import code, link
from structlog import get_logger

from bot.core.follow_transaction import (
    FollowTransaction,
    FollowTransactionCommitResult,
    PodcastIdentifier,
    PodcastIdentifierType,
)
from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_feed_url, is_ppid

log = get_logger()
router = Router()
router.message.middleware(DatabaseMiddleware())

MAX_IDENTIFIERS = 20


def format_failed_identifier(failed: FollowTransactionCommitResult.Failed) -> str:
    if failed.podcast_title:
        return link(failed.podcast_title, failed.podcast_link)

    if failed.podcast_identifier.type == PodcastIdentifierType.PPID:
        return code(failed.podcast_identifier.value)

    return failed.podcast_identifier.value


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
    transaction = FollowTransaction(user)
    invalid_identifiers: list[str] = (
        []
    )  # list of identifiers that did not pass validation

    for identifier in identifiers:
        if is_ppid(identifier):
            await transaction.follow_podcast_by_ppid(identifier)
        elif is_feed_url(identifier):
            await transaction.follow_podcast_by_feed_url(identifier)
        else:
            invalid_identifiers.append(identifier)
            continue

    result = await transaction.commit()

    response: str
    if result.succeeded:
        response = "✨ You have successfully subscribed to the following podcasts:\n"
        for podcast in result.succeeded:
            response += f"👌 {link(podcast.podcast_title, podcast.podcast_link)}\n"

        response += (
            "\n"
            "From now on, you will receive new episodes of these podcasts as soon as they are released!\n"
            "\n"
        )

        for identifier in invalid_identifiers:
            response += (
                f"⚠ ️{identifier}: identifier does not look like a valid URL or PPID"
            )

        for failed in result.failed:
            response += f"⚠  {format_failed_identifier(failed)}: {failed.message}\n"

        response += (
            "\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow from podcasts."
        )

        await state.clear()

    else:
        response = "❌ Failed to subscribe to any of the provided podcasts.\n\n"
        for failed in result.failed:
            response += f"⚠ ️{format_failed_identifier(failed)}: {failed.message}\n"

        response += "\n" "Please try again or /cancel this action."

    await message.answer(response, disable_web_page_preview=len(result.succeeded) != 1)


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
