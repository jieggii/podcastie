from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .models import User, Podcast


async def init(host: str, port: int, db_name: str):
    client = AsyncIOMotorClient(host, port)
    await init_beanie(database=client[db_name], document_models=[User, Podcast])
