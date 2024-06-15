from datetime import datetime

import podcastie_rss
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger
from podcastie_database.models import Podcast, User

from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.ppid import generate_ppid
from bot.validators import is_feed_url, is_ppid

router = Router()
router.message.middleware(DatabaseMiddleware())


@router.message(States.follow)
async def handle_follow_state(message: Message, state: FSMContext, user: User) -> None:
    podcast_identifier = message.text

    podcast: Podcast | None = None

    if is_ppid(podcast_identifier):
        # find podcast by PPID:
        ppid = podcast_identifier

        podcast = await Podcast.find_one(Podcast.ppid == ppid)
        if not podcast:
            await message.answer(
                "I checked twice but could not find podcast with this PPID. "
                "Please try again or /cancel this action.",
            )
            return

    elif is_feed_url(podcast_identifier):
        # find or save podcast by feed URL:
        feed_url = podcast_identifier

        podcast = await Podcast.find_one(Podcast.feed_url == feed_url)
        if not podcast:
            # try retrieving the podcast information by RSS feed URL:
            try:
                feed = await podcastie_rss.fetch_podcast(feed_url, max_episodes=1)

            except (
                podcastie_rss.InvalidFeedError,
                podcastie_rss.UntitledPodcastError,
            ) as e:
                logger.info(f"could not parse podcast feed {feed_url=}, {e=}")
                await message.answer(  # todo: add link to a document explaining requirements to the RSS feed (refine message)
                    "⛔ I could not parse this RSS feed. "
                    "Please try again or /cancel this action."
                )
                return

            except Exception as e:
                logger.info(f"could not fetch podcast feed {feed_url=}, {e}")
                await message.answer(
                    "⛔ I could not fetch the podcast RSS feed."
                )  # todo: refine message
                return

            # store the podcast in the database:
            latest_episode_date: datetime | None = None
            if feed.episodes:
                latest_episode_date = feed.episodes[0].publication_date

            podcast = Podcast(
                ppid=generate_ppid(feed.title),
                title=feed.title,
                link=feed.link,
                feed_url=feed_url,
                latest_episode_date=latest_episode_date,
            )
            await podcast.insert()
            logger.info(f"stored a new podcast podcast={podcast}")

    else:
        await message.answer("🤔 This does not look like URL or valid ppid!")
        return

    # fail if user already follows this podcast:
    if podcast.id in user.following_podcasts:
        await state.clear()
        await message.answer(f"🤔 You already follow {podcast.title} podcast!")
        return

    # add podcast feed to user's subscription URLs:
    user.following_podcasts.append(podcast.id)
    await user.save()

    await state.clear()

    fmt_podcast_title = (
        f'<a href="{podcast.link}">{podcast.title}</a>'
        if podcast.link
        else podcast.title
    )
    await message.answer(
        f"You have successfully subscribed to {fmt_podcast_title}.\n"
        f"From now on, you will receive messages with new episodes of this podcast!\n\n"
        "Use /list to list your subscriptions and /unfollow to unfollow from podcasts.",
    )


@router.message(Command("follow"))
async def handle_follow_command(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(States.follow)
    await message.answer(
        "📻 Please send me the RSS feed URL or PPID of the podcast.\n"
        "\n"
        "Use /cancel to cancel this action.",
    )
