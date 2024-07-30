import time
import hashlib

import podcastie_rss
import pymongo
from beanie import Document, Indexed
from pydantic import BaseModel
from string import punctuation


_TITLE_SLUG_FORBIDDEN_CHARS = set(punctuation)
_FEED_URL_HASH_PREFIX_LEN = 7


def generate_title_slug(title: str) -> str:
    slug_chars: list[str] = []
    for c in title:
        if c.isspace() or c in _TITLE_SLUG_FORBIDDEN_CHARS:
            continue
        slug_chars.append(c.lower())

    return "".join(slug_chars)

def _generate_feed_url_hash(feed_url: str) -> str:
    return hashlib.sha256(feed_url.encode(), usedforsecurity=False).hexdigest()


class PodcastMeta(BaseModel):
    title: str

    description: str | None
    link: str | None
    cover_url: str | None

    def hash(self) -> str:
        target = f"{self.title}{self.description}{self.link}{self.cover_url}"
        hashsum = hashlib.sha256(target.encode(), usedforsecurity=False).hexdigest()
        return hashsum

class PodcastLatestEpisodeInfo(BaseModel):
    check_ts: int
    check_success: bool
    publication_ts: int | None


class Podcast(Document):
    feed_url: Indexed(str, unique=True)
    feed_url_hash_prefix: Indexed(str, unique=True)
    title_slug: str

    meta: PodcastMeta
    latest_episode_info: PodcastLatestEpisodeInfo

    class Settings:
        name = "podcasts"
        indexes = [
            [
                ("title_slug", pymongo.TEXT),
                ("meta.title", pymongo.TEXT),
            ]
        ]

    @classmethod
    def from_feed(cls, feed: podcastie_rss.Feed, feed_url: str):
        return cls(
            feed_url=feed_url,
            feed_url_hash_prefix=_generate_feed_url_hash(feed_url)[:_FEED_URL_HASH_PREFIX_LEN],
            title_slug=generate_title_slug(feed.title),

            meta=PodcastMeta(
                title=feed.title,
                description=feed.description,
                link=feed.link,
                cover_url=feed.cover_url,
            ),
            latest_episode_info=PodcastLatestEpisodeInfo(
                check_ts=int(time.time()),
                check_success=True,
                publication_ts=feed.latest_episode.published if feed.latest_episode else None
            )
        )

    @property
    def ppid(self) -> str:
        return f"{self.title_slug}#{self.feed_url_hash_prefix}"

    def __repr__(self) -> str:
        return self.__str__()
