from aiogram import Bot
from aiogram.enums import ChatAction
from bot.core import opml
import typing

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.aiogram_callback_view.callback_view import CallbackView
from bot.aiogram_callback_view.util import answer_entrypoint_event
from bot.callback_data.entrypoints import FindViewEntrypointCallbackData, ImportViewEntrypointCallbackData, \
    MenuViewEntrypointCallbackData
from bot.core.user import User


def _build_result_reply_markup(text: str) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text=text, callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()

def _build_call_to_action_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Find a podcast", callback_data=FindViewEntrypointCallbackData())
    kbd.button(text="Import podcasts", callback_data=ImportViewEntrypointCallbackData())

    return kbd.as_markup()


class ExportView(CallbackView):
    async def handle_entrypoint(self, event: Message | CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        bot: Bot = data["bot"]
        user: User = data["user"]

        subscriptions = await user.get_following_podcasts()
        if not subscriptions:
            if isinstance(event, CallbackQuery):
                await event.answer("You don't follow any podcasts yet!", show_alert=True)
                return
            elif isinstance(event, Message):
                await event.answer("You don't follow any podcasts yet!", reply_markup=_build_call_to_action_reply_markup())
                return
            else:
                raise ValueError("unexpected event type")

        content = opml.generate_opml(subscriptions)
        file = BufferedInputFile(content.encode(), "Podcastie.opml.xml")

        await bot.send_chat_action(event.from_user.id, ChatAction.UPLOAD_DOCUMENT)

        if isinstance(event, CallbackQuery):
            await event.answer("File attached")
            await event.message.answer_document(file, caption="Here are your subscriptions in OPML format", )

            text = "You can use this file. Anything else?"
            await event.message.answer(text, reply_markup=_build_result_reply_markup("<< Menu"))

        elif isinstance(event, Message):
            await event.answer_document(file, caption="Use this file to import subs in other apps")
            await event.answer("📄 Here are your subscriptions in OPML format. Anything else?", reply_markup=_build_result_reply_markup("Menu"))

        else:
            raise ValueError("unexpected event type")