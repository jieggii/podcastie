import asyncio
import logging
import sys

import aiogram.loggers
import podcastie_database
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.env import env
from bot.router import command
from bot.router import inline_query


def setup_logging():
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    aiogram.loggers.webhook = structlog.get_logger()
    logging.getLogger("aiogram.webhook").setLevel(logging.WARNING)

    aiogram.loggers.middlewares = structlog.get_logger()
    logging.getLogger("aiogram.middlewares").setLevel(logging.WARNING)

    aiogram.loggers.event = structlog.get_logger()
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)

    aiogram.loggers.dispatcher = structlog.get_logger()
    logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)

    aiogram.loggers.scene = structlog.get_logger()
    logging.getLogger("aiogram.scene").setLevel(logging.WARNING)


async def main() -> None:
    setup_logging()

    log = structlog.get_logger()

    # init database:
    log.info(
        "Connecting to the database...",
        host=env.Mongo.HOST,
        port=env.Mongo.PORT,
        database=env.Mongo.DATABASE,
    )
    await podcastie_database.init(
        env.Mongo.HOST,
        env.Mongo.PORT,
        env.Mongo.DATABASE,
    )

    # create and setup router:
    dp = Dispatcher()

    # note: be sure to register cancel_command.router first so that it is the first router to handle /cancel command
    dp.include_router(command.cancel.router)
    dp.include_routers(
        command.about.router,
        command.export.router,
        command.faq.router,
        command.follow.router,
        command.help.router,
        command.import_.router,
        command.list.router,
        command.search.router,
        command.start.router,
        command.unfollow.router,
    )
    dp.include_router(inline_query.router)

    # create and start bot:
    bot = Bot(
        token=env.Bot.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp["bot"] = bot

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
