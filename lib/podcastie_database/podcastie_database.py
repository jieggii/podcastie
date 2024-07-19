import random
import time

import podcastie_rss
from beanie import Document, PydanticObjectId, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


def generate_ppid(podcast_title: str) -> str:
    ppid = podcast_title.lower().strip()
    ppid = "".join(ppid.split())
    ppid = ppid[:15]
    ppid = f"{ppid}#{random.randint(1000, 9999)}"
    return ppid


class Podcast(Document):
    ppid: str
    title: str
    feed_url: str

    link: str | None

    latest_episode_checked: int
    latest_episode_check_successful: bool
    latest_episode_publication_ts: int | None = None

    class Settings:
        name = "podcasts"

    @classmethod
    def from_feed(cls, feed: podcastie_rss.Feed, feed_url: str):
        return cls(
            ppid=generate_ppid(feed.title),
            title=feed.title,
            feed_url=feed_url,
            link=feed.link,
            latest_episode_checked=int(time.time()),
            latest_episode_check_successful=True,
            latest_episode_publication_ts=feed.latest_episode.published if feed.latest_episode else None,
        )

    def __repr__(self) -> str:
        return self.__str__()


class User(Document):
    user_id: int
    following_podcasts: list[PydanticObjectId] = []

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return self.__str__()


async def init(host: str, port: int, db_name: str):
    client = AsyncIOMotorClient(host, port)
    await init_beanie(database=client[db_name], document_models=[User, Podcast])
