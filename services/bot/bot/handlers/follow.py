import time

import aiohttp
import podcastie_rss
from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from podcastie_database.models import Podcast, User
from structlog import get_logger

from podcastie_telegram_html import link

from bot.fsm import States
from bot.middlewares import DatabaseMiddleware
from bot.ppid import generate_ppid
from bot.validators import is_feed_url, is_ppid

log = get_logger()
router = Router()
router.message.middleware(DatabaseMiddleware())


MAX_IDENTIFIERS = 20


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

    # parse identifiers:
    podcasts: list[Podcast] = []  # list of podcasts user will follow
    errors: list[str] = []  # list of errors when attempting to follow podcast

    for identifier in identifiers:
        podcast: Podcast

        if is_ppid(identifier):
            # find podcast by PPID:
            ppid = identifier
            podcast = await Podcast.find_one(Podcast.ppid == ppid)

            if podcast:
                # skip podcast if it is already considered:
                if podcast in podcasts:
                    continue

                # skip podcast if user already follows it:
                if podcast.id in user.following_podcasts:
                    errors.append(f"you already follow {link(podcast.title, podcast.link)}")
                    continue

                podcasts.append(podcast)

            else:
                errors.append(f"PPID <code>{ppid}</code> was not found in the database")
                continue

        elif is_feed_url(identifier):
            # find or save podcast by feed URL:
            url = identifier
            podcast = await Podcast.find_one(Podcast.feed_url == url)
            if podcast:
                # skip podcast if it is already considered:
                if podcast in podcasts:
                    continue

                # skip podcast if the user already follows this podcast:
                if podcast.id in user.following_podcasts:
                    errors.append(f"you already follow {link(podcast.title, podcast.link)}")
                    continue

                podcasts.append(podcast)

            else:
                # try retrieving the podcast information by RSS feed URL:
                try:
                    feed = await podcastie_rss.fetch_podcast(url)

                except aiohttp.ClientConnectorError as e:
                    log.info("could not fetch feed", e=e)
                    errors.append(f"could not fetch {url}")
                    continue

                except podcastie_rss.MalformedFeedFormatError as e:
                    log.info("refused to follow feed: it has malformed format", e=e)
                    errors.append(f"RSS feed at {url} has malformed format")
                    continue

                except podcastie_rss.FeedDidNotPassValidation as e:
                    log.info("refused to follow feed: it did not pass validation", e=e)
                    errors.append(
                        f"RSS feed at {url} did not pass my validation (read more here todo)"
                    )
                    continue

                except Exception as e:
                    log.exception("unexpected exception when fetching feed", e=e)
                    errors.append(f"unexpected error when fetching RSS feed at {url}")
                    continue

                # store the podcast in the database:
                latest_episode_published: int | None = None
                if feed.latest_episode:
                    latest_episode_published = feed.latest_episode.published

                podcast = Podcast(
                    ppid=generate_ppid(feed.title),
                    title=feed.title,
                    link=feed.link,
                    feed_url=identifier,
                    latest_episode_checked=int(time.time()),
                    latest_episode_check_successful=True,
                    latest_episode_publication_ts=latest_episode_published,
                )
                log.info("storing new podcast", podcast_title=podcast.title)
                await podcast.insert()
                podcasts.append(podcast)

        else:
            errors.append(
                f'identifier "{identifier}" does not look like a valid URL or PPID'
            )
            continue

    # add podcasts to user's subscriptions:
    user.following_podcasts.extend([podcast.id for podcast in podcasts])
    await user.save()

    response = ""

    if podcasts:
        if not errors:
            response += (
                "✨ You have successfully subscribed to all provided podcasts:\n"
            )
        else:
            response += "✨ You have successfully subscribed to some of the provided podcasts:\n"

        for podcast in podcasts:
            response += f"👌 {link(podcast.title, podcast.link)}\n"

        if errors:
            response += "\n"
            for error in errors:
                fmt_error = f"{error[0].upper()}{error[1:]}"
                response += f"⚠  {fmt_error}\n"

    else:
        response = "❌ Failed to subscribe to any of the provided podcasts.\n\n"
        for error in errors:
            fmt_error = f"{error[0].upper()}{error[1:]}"
            response += f"⚠ ️{fmt_error}\n"

    # add appendix:
    if podcasts:
        response += (
            "\n"
            "From now on, you will receive new episodes of these podcasts as soon as they are released!"
            "\n\n"
            "Use /list to get list of your subscriptions and /unfollow to unfollow from podcasts."
        )
        await state.clear()

    else:
        response += "\n" "Please try again or /cancel this action."

    await message.answer(response, disable_web_page_preview=len(podcasts) != 1)


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
