from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database import Podcast, User

from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.validators import is_ppid

router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(States.UNFOLLOW)
async def handle_unfollow_state(
    message: Message, state: FSMContext, user: User
) -> None:
    ppid = message.text
    if not is_ppid(ppid):
        await message.answer(
            "This message does not look like a correct PPID. Please try again or /cancel this action."
        )
        return

    podcast = await Podcast.find_one(Podcast.ppid == ppid)
    if not podcast:
        await message.answer(
            "I checked twice and could not find podcast with this PPID in my database. "
            "Are you sure it is correct? Please try again or /cancel this action."
        )
        return

    try:
        user.following_podcasts.remove(podcast.id)
        await user.save()

        # todo: remove podcast from the database if noone follows it anymore

        await state.clear()
        await message.answer(
            f"Good. I have successfully unsubscribed you from {podcast.title}"
        )

    except ValueError:
        await message.answer("Well... But you are not following this podcast anyway!")


@router.message(Command("unfollow"))
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
