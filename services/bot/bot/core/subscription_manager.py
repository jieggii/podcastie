from dataclasses import dataclass
from enum import Enum

import aiohttp
import podcastie_rss
import structlog
from podcastie_database.models.podcast import Podcast
from podcastie_database.models.user import User

from bot.core.ppid import extract_feed_url_hash_prefix_from_ppid

log = structlog.get_logger()


class _PodcastNotFound(Exception):
    pass


class BadFeedException(Exception):
    pass


class PodcastIdentifierType(str, Enum):
    PPID = "ppid"
    FEED_URL = "feed_url"


@dataclass
class PodcastIdentifier:
    value: str
    type: PodcastIdentifierType


async def fetch_podcast_feed(feed_url: str) -> podcastie_rss.Feed:
    try:
        return await podcastie_rss.fetch_feed(feed_url)

    except aiohttp.ClientConnectorError:
        raise BadFeedException("could not fetch feed")

    except podcastie_rss.MalformedFeedFormatError:
        raise BadFeedException("feed has malformed format")

    except podcastie_rss.MissingFeedTitleError as e:
        raise BadFeedException("feed does not contain podcast title")

    except Exception as e:
        log.exception("unexpected exception when attempting to fetch feed", e=e)
        raise BadFeedException("unexpected error when attempting to fetch feed")


class ActionType(str, Enum):
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"


@dataclass
class Action:
    target_identifier: PodcastIdentifier
    type: ActionType


@dataclass
class _TransactionResult:
    action: Action


@dataclass
class TransactionResultSuccess(_TransactionResult):
    podcast_title: str
    podcast_link: str


@dataclass
class TransactionResultFailure(_TransactionResult):
    error_message: str
    podcast_title: str | None = None
    podcast_link: str | None = None


async def _resolve_target(action: Action) -> Podcast:
    """
    Resolves target podcast for provided action.
    Creates a new podcast in the database if necessary.
    """
    match action.target_identifier.type:
        case PodcastIdentifierType.PPID:
            ppid = action.target_identifier.value
            feed_url_hash_prefix = extract_feed_url_hash_prefix_from_ppid(ppid)

            podcast = await Podcast.find_one(
                Podcast.feed_url_hash_prefix == feed_url_hash_prefix
            )
            if not podcast:
                raise _PodcastNotFound("podcast with given PPID was not found")
            return podcast

        case PodcastIdentifierType.FEED_URL:
            feed_url = action.target_identifier.value

            podcast = await Podcast.find_one(Podcast.feed_url == feed_url)
            if podcast:
                return podcast

            match action.type:
                case ActionType.FOLLOW:
                    feed: podcastie_rss.Feed = await fetch_podcast_feed(feed_url)
                    podcast = Podcast.from_feed(feed, feed_url)
                    await podcast.insert()
                    return podcast

                case ActionType.UNFOLLOW:
                    raise _PodcastNotFound("podcast with given feed URL was not found")

                case _:
                    raise ValueError("unexpected action type")

        case _:
            raise ValueError("unexpected target identifier type")


class SubscriptionsManager:
    _user: User
    _actions: list[Action]
    _commited: bool

    def __init__(self, user: User):
        self._user = user
        self._actions = []
        self._commited = False

    async def _follow(self, identifier: str, identifier_type: PodcastIdentifierType):
        self._actions.append(
            Action(
                type=ActionType.FOLLOW,
                target_identifier=PodcastIdentifier(
                    value=identifier, type=identifier_type
                ),
            )
        )

    async def _unfollow(self, identifier: str, identifier_type: PodcastIdentifierType):
        self._actions.append(
            Action(
                type=ActionType.UNFOLLOW,
                target_identifier=PodcastIdentifier(
                    value=identifier, type=identifier_type
                ),
            )
        )

    async def follow_by_ppid(self, ppid: str) -> None:
        await self._follow(ppid, PodcastIdentifierType.PPID)

    async def follow_by_feed_url(self, feed_url: str) -> None:
        await self._follow(feed_url, PodcastIdentifierType.FEED_URL)

    async def unfollow_by_ppid(self, ppid: str) -> None:
        await self._unfollow(ppid, PodcastIdentifierType.PPID)

    async def commit(
        self,
    ) -> tuple[list[TransactionResultSuccess], list[TransactionResultFailure]]:
        """Commits subscription transaction.s"""
        if self._commited:
            raise RuntimeError("transaction has already been commited")
        self._commited = True

        success_results: list[TransactionResultSuccess] = []
        failure_results: list[TransactionResultFailure] = []

        for action in self._actions:
            try:
                podcast = await _resolve_target(action)
            except Exception as e:
                match e:
                    case _PodcastNotFound():
                        failure_results.append(
                            TransactionResultFailure(
                                action=action, error_message=str(e)
                            )
                        )
                    case BadFeedException():
                        failure_results.append(
                            TransactionResultFailure(
                                action=action, error_message=str(e)
                            )
                        )
                    case _:
                        failure_results.append(
                            TransactionResultFailure(
                                action=action,
                                error_message="unexpected error when resolving podcast",
                            )
                        )
                continue

            user_follows_podcast = podcast.id in self._user.following_podcasts
            match action.type:
                case ActionType.FOLLOW:
                    if user_follows_podcast:
                        failure_results.append(
                            TransactionResultFailure(
                                action=action,
                                error_message="you already follow this podcast",
                                podcast_title=podcast.meta.title,
                                podcast_link=podcast.meta.title,
                            )
                        )
                        continue

                    self._user.following_podcasts.append(podcast.id)
                    success_results.append(
                        TransactionResultSuccess(
                            action=action,
                            podcast_title=podcast.meta.title,
                            podcast_link=podcast.meta.link,
                        )
                    )

                case ActionType.UNFOLLOW:
                    if not user_follows_podcast:
                        failure_results.append(
                            TransactionResultFailure(
                                action=action,
                                error_message="you don't follow this podcast",
                                podcast_title=podcast.meta.title,
                                podcast_link=podcast.meta.link,
                            )
                        )
                        continue

                    self._user.following_podcasts.remove(podcast.id)
                    success_results.append(
                        TransactionResultSuccess(
                            action=action,
                            podcast_title=podcast.meta.title,
                            podcast_link=podcast.meta.link,
                        )
                    )

                case _:
                    raise ValueError("unexpected action type")

        await self._user.save()
        return success_results, failure_results
