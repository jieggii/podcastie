import asyncio

import podcastie_configs
import podcastie_database
import structlog

from notifier.env import env
from notifier.notifier import Notifier


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    log.info("connecting to the database")
    await podcastie_database.init(
        env.Mongo.HOST,
        env.Mongo.PORT,
        podcastie_configs.get_value(env.Mongo.DATABASE, env.Mongo.DATABASE_FILE),
    )

    notifier = Notifier(
        bot_token=podcastie_configs.get_value(env.Bot.TOKEN, env.Bot.TOKEN_FILE),
        poll_interval=60,  # todo: env var
    )

    log.info("starting notifier")
    await notifier.start()


if __name__ == "__main__":
    asyncio.run(main())
