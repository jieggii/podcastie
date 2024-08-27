import typing

from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_core.service import user_subscriptions
from podcastie_core.user import User

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    FindViewEntrypointCallbackData,
    ImportViewEntrypointCallbackData,
    MenuViewEntrypointCallbackData,
)
from bot.utils import opml


def _build_result_reply_markup(text: str) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text=text, callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()


class ExportView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        bot: Bot = data["bot"]
        user: User = data["user"]

        subscriptions = await user_subscriptions(user)
        if not subscriptions:
            await event.message.edit_text(
                "🔕 You aren't following any podcasts yet.",
                reply_markup=_build_result_reply_markup("« Back"),
            )
            return

        content = opml.generate_opml(subscriptions)
        file = BufferedInputFile(content.encode(), "Podcastie.opml.xml")

        await bot.send_chat_action(event.from_user.id, ChatAction.UPLOAD_DOCUMENT)

        await event.answer()
        await event.message.answer_document(
            file,
            caption="📄 Here are your subscriptions in OPML format.",
        )
        await event.message.answer(
            "You can import this file into any other podcast app.",
            reply_markup=_build_result_reply_markup("« Menu"),
        )
