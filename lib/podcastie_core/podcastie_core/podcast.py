import hashlib
import string
import time

import podcastie_rss
from beanie import PydanticObjectId
from podcastie_database.models.podcast_model import (
    PodcastLatestEpisodeInfo,
    PodcastMeta,
)
from podcastie_database.models.podcast_model import PodcastModel


PODCAST_FEED_URL_HASH_PREFIX_LEN = 8


def _generate_feed_url_hash_prefix(feed_url: str, length: int) -> str:
    digest = hashlib.sha256(feed_url.encode(), usedforsecurity=False).hexdigest()
    return digest[:length]


_TITLE_SLUG_FORBIDDEN_CHARS = set(string.punctuation)


def _generate_podcast_title_slug(title: str) -> str:
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
    _model: PodcastModel

    def __init__(self, model: PodcastModel):
        self._model = model

    @property
    def model(self) -> PodcastModel:
        return self._model

    @classmethod
    async def from_object_id(cls, object_id: PydanticObjectId):
        podcast = await PodcastModel.get(object_id)
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url(cls, feed_url: str):
        podcast = await PodcastModel.find_one(
            PodcastModel.feed_url == feed_url
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url_hash_prefix(cls, feed_url_hash_prefix: str):
        podcast = await PodcastModel.find_one(
            PodcastModel.feed_url_hash_prefix == feed_url_hash_prefix
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def new_from_feed(cls, feed: podcastie_rss.Feed, feed_url: str):
        global PODCAST_FEED_URL_HASH_PREFIX_LEN

        db_object = PodcastModel(
            feed_url=feed_url,
            feed_url_hash_prefix=_generate_feed_url_hash_prefix(
                feed_url, PODCAST_FEED_URL_HASH_PREFIX_LEN
            ),
            meta=PodcastMeta(
                title=feed.title,
                title_slug=_generate_podcast_title_slug(feed.title),
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
        except podcastie_rss.FeedError as e:
            raise PodcastFeedError("failed to fetch podcast feed") from e

        return await cls.new_from_feed(feed, feed_url)
