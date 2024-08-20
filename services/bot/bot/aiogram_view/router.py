from typing import Any, Type

import aiogram
from aiogram import BaseMiddleware
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.handlers import BaseHandler, CallbackQueryHandler
from aiogram.types import Message

from bot.aiogram_view._handler import (
    new_entrypoint_callback_query_handler,
    new_entrypoint_command_handler,
    new_state_handler,
)
from bot.aiogram_view.entrypoint_callback_data import EntrypointCallbackData
from bot.aiogram_view.view import View


class ViewRouter(aiogram.Router):
    def __init__(
        self,
        view: View,
        entrypoint_callback_data_type: Type[EntrypointCallbackData] | None = None,
        entrypoint_command: str | None = None,
        handle_state: State | None = None,
        entrypoint_handler_middlewares: list[BaseMiddleware] | None = None,
        state_handler_middlewares: list[BaseMiddleware] | None = None,
    ):
        if not (entrypoint_callback_data_type or entrypoint_command):
            raise ValueError(
                "neither entrypoint_callback_data_type nor entrypoint_command params were provided, expected at least one of them"
            )

        super().__init__(name=view.__class__.__name__)

        # include router for callback query entrypoint handler if needed:
        if entrypoint_callback_data_type:
            self.include_router(
                self._new_entrypoint_callback_query_router(
                    handler=new_entrypoint_callback_query_handler(view),
                    entrypoint_callback_data=entrypoint_callback_data_type,
                    middlewares=entrypoint_handler_middlewares,
                )
            )

        # include router for command entrypoint handler if needed:
        if entrypoint_command:
            self.include_router(
                self._new_entrypoint_command_router(
                    handler=new_entrypoint_command_handler(view),
                    command=entrypoint_command,
                    middlewares=entrypoint_handler_middlewares,
                )
            )

        # include router for state handler if needed:
        if handle_state:
            self.include_router(
                self._new_state_router(
                    handler=new_state_handler(view),
                    handle_state=handle_state,
                    middlewares=state_handler_middlewares,
                )
            )

    def _new_sub_router(
        self,
        name: str,
        handler: Type[BaseHandler[Message]] | Type[CallbackQueryHandler],
        filter: CallbackType,
        middlewares: list[BaseMiddleware] | None = None,
    ):
        router = aiogram.Router(name=f"{self.name}/{name}")

        observer: TelegramEventObserver
        if issubclass(handler, CallbackQueryHandler):
            observer = router.callback_query
        elif issubclass(handler, BaseHandler):
            observer = router.message
        else:
            raise ValueError(f"unexpected handler type {handler} {type(handler)}")

        observer.register(handler, filter)
        if middlewares:
            for m in middlewares:
                observer.middleware(m)

        return router

    def _new_entrypoint_callback_query_router(
        self,
        handler: Type[CallbackQueryHandler],
        entrypoint_callback_data: Type[EntrypointCallbackData],
        middlewares: list[BaseMiddleware] | None = None,
    ) -> aiogram.Router:
        return self._new_sub_router(
            "entrypoint_callback_query",
            handler,
            entrypoint_callback_data.filter(),
            middlewares,
        )

    def _new_entrypoint_command_router(
        self,
        handler: Type[BaseHandler[Message]],
        command: str,
        middlewares: list[BaseMiddleware] | None = None,
    ) -> aiogram.Router:
        return self._new_sub_router(
            "entrypoint_command_router",
            handler,
            Command(command),
            middlewares,
        )

    def _new_state_router(
        self,
        handler: Type[BaseHandler[Message]],
        handle_state: State,
        middlewares: list[BaseMiddleware] | None = None,
    ) -> aiogram.Router:
        return self._new_sub_router(
            "state",
            handler,
            handle_state,
            middlewares,
        )
