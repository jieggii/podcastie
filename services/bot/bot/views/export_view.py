from aiogram import Bot
from aiogram.enums import ChatAction
from bot.core import opml
import typing

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import FindViewEntrypointCallbackData, ImportViewEntrypointCallbackData, MenuViewEntrypointCallbackData
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


class ExportView(View):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        bot: Bot = data["bot"]
        user: User = data["user"]

        subscriptions = await user.get_following_podcasts()
        if not subscriptions:
            await event.answer("You don't follow any podcasts yet.", show_alert=True)
            return

        content = opml.generate_opml(subscriptions)
        file = BufferedInputFile(content.encode(), "Podcastie.opml.xml")

        await bot.send_chat_action(event.from_user.id, ChatAction.UPLOAD_DOCUMENT)

        await event.answer()
        await event.message.answer_document(file, caption="Here are your subscriptions in OPML format", )

        text = "You can import this file in any other podcast app."
        await event.message.answer(text, reply_markup=_build_result_reply_markup("<< Menu"))

