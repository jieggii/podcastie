from dataclasses import dataclass, field
from enum import Enum
from typing import NoReturn

import aiohttp
import podcastie_rss
import structlog
from podcastie_database import Podcast, User

log = structlog.get_logger()


class _PodcastPPIDNotFound(Exception):
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


@dataclass
class FollowTransactionCommitResult:
    @dataclass
    class Succeeded:
        podcast_title: str
        podcast_link: str

    @dataclass
    class Failed:
        podcast_identifier: PodcastIdentifier
        message: str
        podcast_title: str | None = None  # podcast title, if known
        podcast_link: str | None = None  # podcast link, if known

    succeeded: list[Succeeded] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)


async def fetch_podcast_feed(feed_url: str) -> NoReturn | podcastie_rss.Feed:
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


async def _resolve_target(identifier: PodcastIdentifier) -> Podcast | NoReturn:
    """
    Resolves target podcast by provided identifier.
    Creates a new podcast in the database if necessary.
    """
    match identifier.type:
        case PodcastIdentifierType.PPID:
            podcast = await Podcast.find_one(Podcast.ppid == identifier.value)
            if not podcast:
                raise _PodcastPPIDNotFound("podcast with given PPID was not found")
            return podcast
        case PodcastIdentifierType.FEED_URL:
            podcast = await Podcast.find_one(Podcast.feed_url == identifier.value)
            if not podcast:
                feed_url = identifier.value
                feed: podcastie_rss.Feed = await fetch_podcast_feed(feed_url)
                podcast = Podcast.from_feed(feed, feed_url)
                await podcast.insert()
            return podcast
        case _:
            raise ValueError("invalid identifier type")


class FollowTransaction:
    _user: User
    _target_identifiers: list[PodcastIdentifier]
    _commited: bool

    def __init__(self, user: User):
        self._user = user
        self._target_identifiers: list[PodcastIdentifier] = []
        self._commited = False

    async def follow_podcast_by_ppid(self, ppid: str) -> None:
        self._target_identifiers.append(
            PodcastIdentifier(value=ppid, type=PodcastIdentifierType.PPID)
        )

    async def follow_podcast_by_feed_url(self, feed_url: str) -> None:
        self._target_identifiers.append(
            PodcastIdentifier(value=feed_url, type=PodcastIdentifierType.FEED_URL)
        )

    async def commit(self) -> FollowTransactionCommitResult:
        """Commits subscription transaction."""
        if self._commited:
            raise RuntimeError("transaction has already been commited")
        self._commited = True

        result = FollowTransactionCommitResult()
        for identifier in self._target_identifiers:
            try:
                podcast = await _resolve_target(identifier)
            except Exception as e:
                match e:
                    case _PodcastPPIDNotFound():
                        result.failed.append(
                            result.Failed(podcast_identifier=identifier, message=str(e))
                        )
                    case BadFeedException():
                        result.failed.append(
                            result.Failed(podcast_identifier=identifier, message=str(e))
                        )
                    case _:
                        result.failed.append(
                            result.Failed(
                                podcast_identifier=identifier,
                                message="unexpected error when resolving podcast",
                            )
                        )
                continue

            if podcast.id in self._user.following_podcasts:
                result.failed.append(
                    result.Failed(
                        podcast_identifier=identifier,
                        message="you already follow this podcast",
                        podcast_title=podcast.title,
                        podcast_link=podcast.link,
                    )
                )
                continue

            self._user.following_podcasts.append(podcast.id)
            result.succeeded.append(
                result.Succeeded(podcast_title=podcast.title, podcast_link=podcast.link)
            )

        await self._user.save()
        return result
