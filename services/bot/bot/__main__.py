import asyncio
import logging
import sys

import aiogram.loggers
import structlog
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.callback_data.entrypoints import MenuViewEntrypointCallbackData, ImportViewEntrypointCallbackData, \
    ExportViewEntrypointCallbackData
from bot.callback_data.entrypoints import PodcastViewEntrypointCallbackData
from bot.callback_data.entrypoints import ShareViewEntrypointCallbackData
from bot.callback_data.entrypoints import SubscriptionsViewEntrypointCallbackData
from bot.fsm import BotState
from bot.middlewares import DatabaseMiddleware
from bot.views.export_view import ExportView
from bot.views.import_view import ImportView
from bot.views.podcast_view import PodcastView
from bot.views.share_view import ShareView
from bot.views.subscriptions_view import SubscriptionsView
from podcastie_database.init import init_database
from bot.views.find_view import FindView
from bot.views.menu_view import MenuView
from bot.aiogram_callback_view.router import ViewRouter
from bot.callback_data.entrypoints import FindViewEntrypointCallbackData

from bot.env import Env
# from bot.router import inline_query
# from bot.router.callback import (
#     menu as menu_callback,
#     find as find_callback,
#     follow as follow_callback,
#     unfollow as unfollow_callback,
#     import_ as import_callback,
#     subscriptions as subscriptions_callback,
#     podcast as podcast_callback,
# )
# from bot.router.command import (
#     start as start_command,
#     menu as menu_command
# )
# from bot.router.state import (
#     find as find_state,
#     import_ as import_state,
# )


def setup_logging():
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    aiogram.loggers.webhook = structlog.get_logger()
    logging.getLogger("aiogram.webhook").setLevel(logging.WARNING)

    aiogram.loggers.middlewares = structlog.get_logger()
    logging.getLogger("aiogram.middlewares").setLevel(logging.DEBUG)

    aiogram.loggers.event = structlog.get_logger()
    logging.getLogger("aiogram.event").setLevel(logging.DEBUG)

    aiogram.loggers.dispatcher = structlog.get_logger()
    logging.getLogger("aiogram.dispatcher").setLevel(logging.DEBUG)

    aiogram.loggers.scene = structlog.get_logger()
    logging.getLogger("aiogram.scene").setLevel(logging.DEBUG)


async def main() -> None:
    setup_logging()

    log = structlog.get_logger()

    # read configuration from env vars:
    env = Env()
    env.populate()

    # init database:
    log.info(
        "Connecting to the database...",
        host=env.Mongo.HOST,
        port=env.Mongo.PORT,
        database=env.Mongo.DATABASE,
    )
    await init_database(
        env.Mongo.HOST,
        env.Mongo.PORT,
        env.Mongo.DATABASE,
    )

    dp = Dispatcher()

    # include view routers:
    dp.include_routers(
        ViewRouter(
            MenuView(),
            MenuViewEntrypointCallbackData,
            entrypoint_command="menu",
            entrypoint_handler_middlewares=[DatabaseMiddleware()]
        ),
        ViewRouter(
            FindView(),
            FindViewEntrypointCallbackData,
            entrypoint_command="find",
            handle_state=BotState.FIND,
            state_handler_middlewares=[DatabaseMiddleware()]
        ),
        ViewRouter(
            ImportView(),
            ImportViewEntrypointCallbackData,
            entrypoint_command="import",
            handle_state=BotState.IMPORT,
            state_handler_middlewares=[DatabaseMiddleware()]
        ),
        ViewRouter(
            ExportView(),
            ExportViewEntrypointCallbackData,
            entrypoint_command="export",
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            SubscriptionsView(),
            SubscriptionsViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()]
        ),
        ViewRouter(
            PodcastView(),
            PodcastViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()]
        ),
        ViewRouter(
            ShareView(),
            ShareViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()]
        )
     )

    # create and start bot:
    bot = Bot(
        token=env.TelegramBot.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp["bot"] = bot

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
