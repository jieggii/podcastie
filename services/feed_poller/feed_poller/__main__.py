import asyncio

import structlog
from podcastie_database.init import init_database

from feed_poller.env import env
from feed_poller.feed_poller import FeedPoller


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    log.info("connecting to the database")
    await init_database(env.Mongo.HOST, env.Mongo.PORT, env.Mongo.DATABASE)

    poller = FeedPoller(
        bot_token=env.Bot.TOKEN,
        poll_interval=env.FeedPoller.INTERVAL,
    )

    log.info("starting feed poller")
    await poller.start()


if __name__ == "__main__":
    asyncio.run(main())
