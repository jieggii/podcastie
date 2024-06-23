import asyncio

import podcastie_configs
import podcastie_database
import structlog

from notifier.env import env
from notifier.notifier import Notifier

MAX_TELEGRAM_AUDIO_FILE_SIZE = 45 * 1024 * 1024  # 45 mb


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    log.info("initializing database")
    await podcastie_database.init(
        env.Mongo.HOST,
        env.Mongo.PORT,
        podcastie_configs.get_value(env.Mongo.DATABASE, env.Mongo.DATABASE_FILE),
    )

    notifier = Notifier(
        bot_token=env.Bot.TOKEN,
        audio_storage_path="/tmp",
        poll_feeds_interval=60,
        log_queue_sizes_interval=10,
        max_telegram_audio_file_size=MAX_TELEGRAM_AUDIO_FILE_SIZE,
    )

    log.info("starting notifier")
    try:
        await notifier.run()
    except asyncio.CancelledError:
        log.info("all notifier asyncio tasks were cancelled")
    finally:
        await notifier.close()


if __name__ == "__main__":
    asyncio.run(main())
