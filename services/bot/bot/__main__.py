import asyncio
import logging
import sys

import aiogram.loggers
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from podcastie_database.init import init_database

from bot.aiogram_view.router import ViewRouter
from bot.callback_data.entrypoints import (
    ExportViewEntrypointCallbackData,
    FindViewEntrypointCallbackData,
    ImportViewEntrypointCallbackData,
    MenuViewEntrypointCallbackData,
    PodcastViewEntrypointCallbackData,
    ShareViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
    UnfollowViewEntrypointCallbackData,
)
from bot.env import Env
from bot.fsm import BotState
from bot.middlewares import DatabaseMiddleware
from bot.views.export_view import ExportView
from bot.views.find_view import FindView
from bot.views.import_view import ImportView
from bot.views.menu_view import MenuView
from bot.views.podcast_view import PodcastView
from bot.views.share_view import ShareView
from bot.views.start_view import StartView
from bot.views.subscriptions_view import SubscriptionsView
from bot.views.unfollow_view import UnfollowView


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
            StartView(),
            entrypoint_command="start",
        ),
        ViewRouter(
            MenuView(),
            entrypoint_callback_data_type=MenuViewEntrypointCallbackData,
            entrypoint_command="menu",
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            FindView(),
            entrypoint_callback_data_type=FindViewEntrypointCallbackData,
            handle_state=BotState.FIND,
            state_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            ImportView(),
            entrypoint_callback_data_type=ImportViewEntrypointCallbackData,
            handle_state=BotState.IMPORT,
            state_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            ExportView(),
            entrypoint_callback_data_type=ExportViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            SubscriptionsView(),
            entrypoint_callback_data_type=SubscriptionsViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            PodcastView(),
            entrypoint_callback_data_type=PodcastViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            ShareView(),
            entrypoint_callback_data_type=ShareViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            UnfollowView(),
            entrypoint_callback_data_type=UnfollowViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
    )

    # create and start bot:
    bot = Bot(
        token=env.TelegramBot.TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML, link_preview_is_disabled=True
        ),
    )
    dp["bot"] = bot

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
