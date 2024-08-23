from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from podcastie_database.models.podcast import PodcastDocument
from podcastie_database.models.user import UserDocument


async def init_database(host: str, port: int, db_name: str):
    client = AsyncIOMotorClient(host, port)
    await init_beanie(database=client[db_name], document_models=[UserDocument, PodcastDocument])
