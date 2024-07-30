import asyncio

from podcastie_database.init import init_database
import structlog

from notifier.env import env
from notifier.notifier import Notifier


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    log.info("connecting to the database")
    await init_database(env.Mongo.HOST, env.Mongo.PORT, env.Mongo.DATABASE)

    notifier = Notifier(
        bot_token=env.Bot.TOKEN,
        poll_interval=env.Notifier.POLL_INTERVAL,
    )

    log.info("starting notifier")
    await notifier.start()


if __name__ == "__main__":
    asyncio.run(main())
