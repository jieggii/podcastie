import hashlib
import string
import time

import podcastie_rss
from beanie import PydanticObjectId
from beanie.operators import Text
from podcastie_database.models.podcast_model import (
    PodcastLatestEpisodeInfo,
    PodcastMeta,
)
from podcastie_database.models.podcast_model import (
    PodcastModel as _PodcastDatabaseModel,
)

PODCAST_FEED_URL_HASH_PREFIX_LEN = 8


def generate_feed_url_hash_prefix(feed_url: str, length: int) -> str:
    digest = hashlib.sha256(feed_url.encode(), usedforsecurity=False).hexdigest()
    return digest[:length]


_TITLE_SLUG_FORBIDDEN_CHARS = set(string.punctuation)


def generate_podcast_title_slug(title: str) -> str:
    slug_chars: list[str] = []
    for c in title:
        if c.isspace() or c in _TITLE_SLUG_FORBIDDEN_CHARS:
            continue
        slug_chars.append(c.lower())

    return "".join(slug_chars)


class PodcastNotFoundError(Exception):
    pass


class PodcastFeedError(Exception):
    pass


class Podcast:
    _db_object: _PodcastDatabaseModel

    def __init__(self, db_object: _PodcastDatabaseModel):
        self._db_object = db_object

    @property
    def db_object(self) -> _PodcastDatabaseModel:
        return self._db_object

    @classmethod
    async def from_object_id(cls, object_id: PydanticObjectId):
        podcast = await _PodcastDatabaseModel.get(object_id)
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url(cls, feed_url: str):
        podcast = await _PodcastDatabaseModel.find_one(
            _PodcastDatabaseModel.feed_url == feed_url
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url_hash_prefix(cls, feed_url_hash_prefix: str):
        podcast = await _PodcastDatabaseModel.find_one(
            _PodcastDatabaseModel.feed_url_hash_prefix == feed_url_hash_prefix
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def new_from_feed(cls, feed: podcastie_rss.Feed, feed_url: str):
        global PODCAST_FEED_URL_HASH_PREFIX_LEN

        db_object = _PodcastDatabaseModel(
            feed_url=feed_url,
            feed_url_hash_prefix=generate_feed_url_hash_prefix(
                feed_url, PODCAST_FEED_URL_HASH_PREFIX_LEN
            ),
            meta=PodcastMeta(
                title=feed.title,
                title_slug=generate_podcast_title_slug(feed.title),
                description=feed.description,
                link=feed.link,
                cover_url=feed.cover_url,
            ),
            latest_episode_info=PodcastLatestEpisodeInfo(
                check_ts=int(time.time()),
                check_success=True,
                publication_ts=(
                    feed.latest_episode.published if feed.latest_episode else None
                ),
            ),
        )

        await db_object.insert()
        return cls(db_object)

    @classmethod
    async def new_from_feed_url(cls, feed_url: str):
        try:
            feed = await podcastie_rss.fetch_feed(feed_url)
        except (
            podcastie_rss.FeedReadError,
            podcastie_rss.FeedParseError,
            podcastie_rss.FeedValidateError,
        ) as e:
            raise PodcastFeedError("failed to fetch podcast feed") from e

        return await cls.new_from_feed(feed, feed_url)


async def search_podcasts(query: str) -> list[Podcast]:
    db_objects = await _PodcastDatabaseModel.find(Text(query)).to_list()
    return [Podcast(p) for p in db_objects]
