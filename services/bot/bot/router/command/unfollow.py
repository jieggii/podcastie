from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models.user import User
from podcastie_telegram_html import tags

from bot.core import subscription_manager
from bot.filters import StatePresenceFilter
from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_ppid

router = Router()
router.message.middleware(DatabaseMiddleware())


def format_failed_transaction_identifier(
    t: subscription_manager.TransactionResultFailure,
):
    if t.podcast_title:
        return tags.link(t.podcast_title, t.podcast_link)
    return tags.code(t.action.target_identifier.value)


@router.message(States.UNFOLLOW)
async def handle_unfollow_state(
    message: Message, state: FSMContext, user: User
) -> None:
    ppid = message.text
    if not is_ppid(ppid):
        await message.answer(
            "This message does not look like a correct PPID.\n"
            "\n"
            "Please try again or /cancel this action."
        )
        return

    manager = subscription_manager.SubscriptionsManager(user)
    await manager.unfollow_by_ppid(ppid)
    succeeded, failed = await manager.commit()

    response: str
    if succeeded:
        transaction = succeeded[0]
        await state.clear()
        response = f"👍 Done. I have successfully unsubscribed you from {tags.link(transaction.podcast_title, transaction.podcast_link)}."

    else:
        transaction = failed[0]
        response = (
            f"⚠️ I failed to unsubscribe you from {format_failed_transaction_identifier(transaction)}. Reason: {transaction.error_message}.\n\n"
            f"Please try again or /cancel this action."
        )

    await message.answer(response, disable_web_page_preview=True)


@router.message(Command("unfollow"), StatePresenceFilter(has_state=False))
async def handle_unfollow_command(message: Message, state: FSMContext) -> None:
    # todo: check if it is a reply to a message with an episode
    # so that we could get ppid from there and simply unfollow the desired podcast
    # without asking for PPID!
    await state.set_state(States.UNFOLLOW)
    await message.answer(
        "Please send me PPID of the podcast you want to stop following.\n"
        "\n"
        "You can use /cancel to cancel this action."
    )
