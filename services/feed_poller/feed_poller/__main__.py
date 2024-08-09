import asyncio

import structlog
from podcastie_database.init import init_database

from feed_poller.env import Env
from feed_poller.episode_broadcaster import EpisodeBroadcaster
from feed_poller.feed_poller import FeedPoller


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    # read configuration from env vars:
    env = Env()
    env.populate()

    log.info("connecting to the database")
    await init_database(env.Mongo.HOST, env.Mongo.PORT, env.Mongo.DATABASE)

    episode_broadcaster = EpisodeBroadcaster(
        bot_api_host=env.TelegramBot.API_HOST,
        bot_api_port=env.TelegramBot.API_PORT,
        bot_token=env.TelegramBot.TOKEN,
    )
    feed_poller = FeedPoller(interval=env.FeedPoller.INTERVAL, new_episode_consumer=episode_broadcaster.add_episode)

    log.info("starting feed poller")
    tasks = [
        episode_broadcaster.run(),
        feed_poller.run(),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
