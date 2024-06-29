import asyncio
import logging
import sys

import podcastie_configs
import podcastie_database
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from structlog import get_logger

from bot.env import env
from bot.handlers import about, cancel, faq, follow, help, list, search, start, unfollow


async def main() -> None:
    # todo: setup logger
    log = get_logger()

    # init database:
    log.info(
        "connecting to the database",
        host=env.Mongo.HOST,
        port=env.Mongo.PORT,
        database=None,
    )  # todo
    await podcastie_database.init(
        env.Mongo.HOST,
        env.Mongo.PORT,
        podcastie_configs.get_value(env.Mongo.DATABASE, env.Mongo.DATABASE_FILE),
    )

    # create and setup router:
    dp = Dispatcher()

    # note: be sure to register cancel.router first so that it is the first router to handle /cancel command
    dp.include_router(cancel.router)
    dp.include_routers(
        about.router,
        faq.router,
        follow.router,
        list.router,
        help.router,
        start.router,
        unfollow.router,
        search.router,
    )

    # create and start bot:
    bot = Bot(
        token=podcastie_configs.get_value(env.Bot.TOKEN, env.Bot.TOKEN_FILE),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    log.info("starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
