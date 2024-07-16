from beanie import Document, PydanticObjectId

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


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
