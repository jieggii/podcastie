import asyncio
import logging
import sys

import podcastie_configs
import podcastie_database
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot import env
from bot.handlers import about, cancel, faq, follow, help, list, start, unfollow


async def main() -> None:
    # init database:
    logger.info("initializing database")
    await podcastie_database.init(
        env.MONGO_HOST,
        env.MONGO_PORT,
        podcastie_configs.get_value(env.MONGO_DATABASE, env.MONGO_DATABASE_FILE),
    )

    # create and setup router:
    dp = Dispatcher()

    # note: be sure to register cancel.router first so that it is the first router to handle /cancel command
    dp.include_router(cancel.router)
    dp.include_routers(
        follow.router,
        unfollow.router,
        list.router,
        start.router,
        help.router,
        faq.router,
        about.router,
    )

    # create and start bot:
    bot = Bot(
        token=podcastie_configs.get_value(env.BOT_TOKEN, env.BOT_TOKEN_FILE),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    logger.info("starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
