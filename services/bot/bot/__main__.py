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
    SearchResultViewEntrypointCallbackData,
    ShareViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
    UnfollowViewEntrypointCallbackData,
)
from bot.env import Env
from bot.fsm import BotState
from bot.handlers import inline_query
from bot.handlers.views.export_view import ExportView
from bot.handlers.views.find_view import FindView
from bot.handlers.views.import_view import ImportView
from bot.handlers.views.menu_view import MenuView
from bot.handlers.views.podcast_view import PodcastView
from bot.handlers.views.search_result_item_view import SearchResultView
from bot.handlers.views.share_view import ShareView
from bot.handlers.views.start_view import StartView
from bot.handlers.views.subscriptions_view import SubscriptionsView
from bot.handlers.views.unfollow_view import UnfollowView
from bot.middlewares import UserMiddleware


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

    # include inline query router:
    dp.include_router(inline_query.router)

    # include view routers:
    dp.include_routers(
        ViewRouter(
            StartView(),
            entrypoint_command="start",
            entrypoint_handler_middlewares=[UserMiddleware(create_user=False)],
        ),
        ViewRouter(
            MenuView(),
            entrypoint_callback_data_type=MenuViewEntrypointCallbackData,
            entrypoint_command="menu",
            # entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            FindView(),
            entrypoint_callback_data_type=FindViewEntrypointCallbackData,
            handle_state=BotState.FIND,
            state_handler_middlewares=[UserMiddleware()],
        ),
        ViewRouter(
            SearchResultView(),
            entrypoint_callback_data_type=SearchResultViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[UserMiddleware()],
        ),
        ViewRouter(
            ImportView(),
            entrypoint_callback_data_type=ImportViewEntrypointCallbackData,
            handle_state=BotState.IMPORT,
            state_handler_middlewares=[UserMiddleware()],
        ),
        ViewRouter(
            ExportView(),
            entrypoint_callback_data_type=ExportViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[UserMiddleware()],
        ),
        ViewRouter(
            SubscriptionsView(),
            entrypoint_callback_data_type=SubscriptionsViewEntrypointCallbackData,
            entrypoint_handler_middlewares=[UserMiddleware()],
        ),
        ViewRouter(
            PodcastView(),
            entrypoint_callback_data_type=PodcastViewEntrypointCallbackData,
            # entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            ShareView(),
            entrypoint_callback_data_type=ShareViewEntrypointCallbackData,
            # entrypoint_handler_middlewares=[DatabaseMiddleware()],
        ),
        ViewRouter(
            UnfollowView(),
            entrypoint_callback_data_type=UnfollowViewEntrypointCallbackData,
            # entrypoint_handler_middlewares=[DatabaseMiddleware()],
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
