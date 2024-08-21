import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.aiogram_view.util import answer_entrypoint_event
from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    ExportViewEntrypointCallbackData,
    FindViewEntrypointCallbackData,
    ImportViewEntrypointCallbackData,
    SubscriptionsViewEntrypointCallbackData,
)
from bot.core.user import User


def _build_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Find a podcast", callback_data=FindViewEntrypointCallbackData())
    kbd.button(
        text=f"My subscriptions",
        callback_data=SubscriptionsViewEntrypointCallbackData(),
    )

    kbd.button(
        text="Import",
        callback_data=ImportViewEntrypointCallbackData(remove_current_markup=True),
    )
    kbd.button(
        text="Export",
        callback_data=ExportViewEntrypointCallbackData(remove_current_markup=True),
    )

    kbd.adjust(2, 2)

    return kbd.as_markup()


def _build_poor_menu_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(
        text="Find a podcast",
        callback_data=FindViewEntrypointCallbackData(remove_current_markup=True),
    )
    kbd.button(
        text="Import subscriptions",
        callback_data=ImportViewEntrypointCallbackData(remove_current_markup=True),
    )

    return kbd.as_markup()


class MenuView(View):
    async def handle_entrypoint(
        self, event: Message | CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        await answer_entrypoint_event(
            event,
            data,
            message_text="🗂️️ What would you like to do?",
            reply_markup=_build_reply_markup(),
        )
