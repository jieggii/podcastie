import asyncio

import structlog
from feed_poller.episode_broadcaster import EpisodeBroadcaster
from podcastie_database.init import init_database

from feed_poller.env import env
from feed_poller.feed_poller import FeedPoller


async def main() -> None:
    log = structlog.get_logger().bind(task="main")

    log.info("connecting to the database")
    await init_database(env.Mongo.HOST, env.Mongo.PORT, env.Mongo.DATABASE)

    episode_broadcaster = EpisodeBroadcaster(
        bot_api_host=env.FeedPoller.BOT_API_HOST,
        bot_api_port=env.FeedPoller.BOT_API_PORT,
        bot_token=env.Bot.TOKEN,
    )
    feed_poller = FeedPoller(
        interval=env.FeedPoller.INTERVAL,
        new_episode_consumer=episode_broadcaster.add_episode
    )

    log.info("starting feed poller")
    tasks = [
        episode_broadcaster.run(),
        feed_poller.run(),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
