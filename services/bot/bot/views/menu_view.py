import typing

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, KeyboardBuilder

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
        text="My subscriptions", callback_data=SubscriptionsViewEntrypointCallbackData()
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
        user: User = data["user"]

        text = "What do you want to do?"

        subscriptions = await user.get_following_podcasts()
        if subscriptions:
            markup = _build_reply_markup()
        else:
            markup = _build_poor_menu_reply_markup()

        await answer_entrypoint_event(event, data, text, reply_markup=markup)
