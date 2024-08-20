from typing import Type, Any

from aiogram.fsm.context import FSMContext
from aiogram.handlers import CallbackQueryHandler, BaseHandler
from aiogram.types import Message
from bot.aiogram_callback_view.callback_view import CallbackView
from bot.aiogram_callback_view.entrypoint_callback_data import EntrypointCallbackData


def new_entrypoint_callback_query_handler(view: CallbackView) -> Type[CallbackQueryHandler]:
    class Handler(CallbackQueryHandler):
        async def handle(self) -> Any:
            callback_data: EntrypointCallbackData = self.data["callback_data"]
            if callback_data.clear_state:
                state: FSMContext = self.data["state"]
                await state.clear()

            # if callback_data.remove_current_markup:
                # await self.event.message.delete()
                # await self.event.message.edit_reply_markup(reply_markup=None)
                # pass

            await view.handle_entrypoint(event=self.event, data=self.data)

    return Handler


def new_entrypoint_command_handler(view: CallbackView) -> Type[BaseHandler[[Message]]]:
    class Handler(BaseHandler[Message]):
        async def handle(self) -> Any:
            await view.handle_entrypoint(event=self.event, data=self.data)

    return Handler


def new_state_handler(view: CallbackView) -> Type[BaseHandler[Message]]:
    class Handler(BaseHandler[Message]):
        async def handle(self) -> Any:
            await view.handle_state(message=self.event, data=self.data)

    return Handler
