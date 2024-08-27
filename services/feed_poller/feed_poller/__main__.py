import asyncio

import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions
from podcastie_database.init import init_database
from podcastie_rss import Episode

from feed_poller.env import Env
from feed_poller.episode_broadcaster import EpisodeBroadcaster
from feed_poller.feed_poller import FeedPoller


def new_bot(bot_token: str, bot_api_host: str, bot_api_port: int) -> Bot:
    session = AiohttpSession(api=TelegramAPIServer.from_base(f"http://{bot_api_host}:{bot_api_port}"))

    return Bot(
        token=bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview=LinkPreviewOptions(is_disabled=True)),
    )


async def main() -> None:
    log: structlog.stdlib.BoundLogger = structlog.get_logger()

    log.info("reading configuration...")
    env = Env()
    env.populate()

    log.info("connecting to the database...")
    await init_database(env.Mongo.HOST, env.Mongo.PORT, env.Mongo.DATABASE)

    episodes_queue: asyncio.Queue[Episode] = asyncio.Queue()

    feed_poller = FeedPoller(episodes_queue, interval=env.FeedPoller.INTERVAL)
    episode_broadcaster = EpisodeBroadcaster(
        episodes_queue,
        bot=new_bot(env.TelegramBot.TOKEN, env.TelegramBot.API_HOST, env.TelegramBot.API_PORT),
        interval=1,
    )

    log.info("starting feed poller...")
    tasks = [
        feed_poller.poll_feeds(),
        episode_broadcaster.broadcast_episodes(),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
