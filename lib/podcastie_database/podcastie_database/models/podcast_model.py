import warnings
from typing import TypedDict

import pymongo
from beanie import Document, Indexed
from pydantic import BaseModel


class PodcastMetaPatch(TypedDict):
    new_title: str
    new_title_slug: str

    new_description: str | None
    new_link: str | None
    new_cover_url: str | None


class PodcastMeta(BaseModel):
    title: str
    title_slug: str

    description: str | None
    link: str | None
    cover_url: str | None

    def hash(self) -> str:
        warnings.warn("PodcastMeta.hash() is not implemented and returns 'hash'")
        return "hash"

    def patch(self, patch: PodcastMetaPatch) -> bool:
        patched = False

        if "new_title" in patch:
            self.title = patch["new_title"]
            patched = True

        if "new_title_slug" in patch:
            self.title_slug = patch["new_title_slug"]
            patched = True

        if "new_description" in patch:
            self.description = patch["new_description"]
            patched = True

        if "new_link" in patch:
            self.link = patch["new_link"]
            patched = True

        if "new_cover_url" in patch:
            self.cover_url = patch["new_cover_url"]
            patched = True

        return patched


class PodcastLatestEpisodeInfo(BaseModel):
    check_ts: int
    check_success: bool
    publication_ts: int | None


class PodcastModel(Document):
    feed_url: Indexed(str, unique=True)
    feed_url_hash_prefix: Indexed(str, unique=True)

    meta: PodcastMeta
    latest_episode_info: PodcastLatestEpisodeInfo

    class Settings:
        name = "podcasts"
        indexes = [
            [
                ("meta.title", pymongo.TEXT),
                ("meta.title_slug", pymongo.TEXT),
            ]
        ]

    def __repr__(self) -> str:
        return self.__str__()
