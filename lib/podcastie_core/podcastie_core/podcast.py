import hashlib
import string
import time

import podcastie_rss
from beanie import PydanticObjectId
from podcastie_database.models.podcast import (
    PodcastCheckModel,
    PodcastMetaModel,

)
from podcastie_database.models.podcast import PodcastDocument


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
    _document: PodcastDocument

    def __init__(self, document: PodcastDocument):
        self._document = document

    @property
    def document(self) -> PodcastDocument:
        return self._document

    @classmethod
    async def from_object_id(cls, object_id: PydanticObjectId):
        podcast = await PodcastDocument.get(object_id)
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url(cls, feed_url: str):
        podcast = await PodcastDocument.find_one(
            PodcastDocument.feed_url == feed_url
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def from_feed_url_hash_prefix(cls, feed_url_hash_prefix: str):
        podcast = await PodcastDocument.find_one(
            PodcastDocument.feed_url_hash_prefix == feed_url_hash_prefix
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")

        return cls(podcast)

    @classmethod
    async def new_from_feed(cls, feed: podcastie_rss.Feed, feed_url: str):
        global PODCAST_FEED_URL_HASH_PREFIX_LEN

        document = PodcastDocument(
            feed_url=feed_url,
            feed_url_hash_prefix=_generate_feed_url_hash_prefix(
                feed_url, PODCAST_FEED_URL_HASH_PREFIX_LEN
            ),
            meta=PodcastMetaModel(
                title=feed.title,
                title_slug=_generate_podcast_title_slug(feed.title),
                description=feed.description,
                link=feed.link,
                cover_url=feed.cover_url,
            ),
            check=PodcastCheckModel(
                timestamp=int(time.time()),
                success=True,
            ),
            latest_episode_publication_timestamp=feed.latest_episode.published if feed.latest_episode else None,
        )

        await document.insert()
        return cls(document)

    @classmethod
    async def new_from_feed_url(cls, feed_url: str):
        try:
            feed = await podcastie_rss.fetch_feed(feed_url)
        except podcastie_rss.FeedError as e:
            raise PodcastFeedError("failed to fetch podcast feed") from e

        return await cls.new_from_feed(feed, feed_url)

    async def save_changes(self) -> None:
        await self._document.save_changes()
