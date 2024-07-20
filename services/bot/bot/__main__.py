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
from bot.command_handlers import (
    about,
    cancel,
    export,
    faq,
    follow,
    help,
    import_,
    list,
    search,
    start,
    unfollow,
)
from bot.inline_handler import inline_query_router


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

    # note: be sure to register cancel.router first so that it is the first router to handle /cancel command
    dp.include_router(cancel.router)
    dp.include_routers(
        about.router,
        export.router,
        faq.router,
        follow.router,
        list.router,
        help.router,
        start.router,
        unfollow.router,
        search.router,
        import_.router,
    )
    dp.include_router(inline_query_router)

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
