import warnings

import pymongo
from beanie import Document, Indexed
from pydantic import BaseModel


class PodcastMetaModel(BaseModel):
    title: str
    title_slug: str

    description: str | None
    link: str | None
    cover_url: str | None

    def hash(self) -> str:
        warnings.warn("PodcastMeta.hash() is not implemented and returns 'hash'")
        return "hash"


class PodcastCheckModel(BaseModel):
    timestamp: int
    success: bool


class PodcastDocument(Document):
    feed_url: Indexed(str, unique=True)
    feed_url_hash_prefix: Indexed(str, unique=True)

    meta: PodcastMetaModel
    check: PodcastCheckModel

    latest_episode_publication_timestamp: int | None

    class Settings:
        name = "podcasts"
        indexes = [
            [
                ("meta.title", pymongo.TEXT),
                ("meta.title_slug", pymongo.TEXT),
            ]
        ]
