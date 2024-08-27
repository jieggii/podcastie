import typing

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from podcastie_core.service import search_podcasts
from podcastie_core.user import User

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    FindViewEntrypointCallbackData,
    MenuViewEntrypointCallbackData,
    SearchResultAction,
    SearchResultViewEntrypointCallbackData,
)
from bot.fsm import BotState
from bot.handlers.views.search_result_item_view import SearchResultView


def _build_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(
        text="« Back to menu",
        callback_data=MenuViewEntrypointCallbackData(clear_state=True),
    )

    return kbd.as_markup()


def _build_result_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Search again", callback_data=FindViewEntrypointCallbackData())
    kbd.button(text="« Menu", callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()


class FindView(View):
    async def handle_entrypoint(
        self, event: CallbackQuery, data: dict[str, typing.Any] | None = None
    ) -> None:
        state: FSMContext = data["state"]

        text = (
            "🔍 In your next message, please send me a podcast title you want to find."
        )
        markup = _build_reply_markup()

        await state.set_state(BotState.FIND)

        await event.message.edit_text(text, reply_markup=markup)

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        state: FSMContext = data["state"]
        bot: Bot = data["bot"]
        user: User = data["user"]

        await state.clear()

        if len(message.text) > 50:  # todo: magic number
            await message.answer(
                "⚠️ The search query is too long.",
                reply_markup=_build_result_reply_markup(),
            )
            return

        headline_message = await message.answer("🔎 Searching for the podcast...")

        podcasts = await search_podcasts(message.text)
        podcasts_len = len(podcasts)
        if podcasts_len == 0:
            await headline_message.edit_text(
                "No podcasts were found matching your search query. "
                "Please try adjusting your keywords.",
                reply_markup=_build_result_reply_markup(),
            )
            return

        await headline_message.edit_text(
            "📨 Sending results to you, please wait a moment..."
        )

        for i, podcast in enumerate(podcasts):
            search_result_view = SearchResultView()

            result_view_data = data.copy()
            result_view_data["user"] = user
            result_view_data["callback_data"] = SearchResultViewEntrypointCallbackData(
                podcast_id=podcast.document.id,
                action=SearchResultAction.send,
                result_number=i + 1,
                total_results=podcasts_len,
            )

            await search_result_view.handle_entrypoint(message, result_view_data)

        await headline_message.edit_text("✨ Here is what I have found:")

        await message.answer(
            "Please use inline buttons to follow podcasts I've send to you.",
            reply_markup=_build_result_reply_markup(),
        )
