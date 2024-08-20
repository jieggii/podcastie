import typing

from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, URLInputFile, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.aiogram_view.view import View
from bot.aiogram_view.util import answer_entrypoint_event
from bot.callback_data.entrypoints import FindViewEntrypointCallbackData
from bot.callback_data.entrypoints import MenuViewEntrypointCallbackData
from bot.core.podcast import Podcast, search_podcasts
from bot.core.user import User
from bot.fsm import BotState
from aiogram import Bot
from podcastie_telegram_html.tags import bold, blockquote


def _build_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()
    kbd.button(text="« Back to menu", callback_data=MenuViewEntrypointCallbackData(clear_state=True))

    return kbd.as_markup()

def _build_result_reply_markup() -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    kbd.button(text="Search again", callback_data=FindViewEntrypointCallbackData())
    kbd.button(text="« Menu", callback_data=MenuViewEntrypointCallbackData())

    return kbd.as_markup()


def _build_podcast_card_reply_markup(podcast: Podcast, user_is_following_podcast: bool) -> InlineKeyboardMarkup:
    kbd = InlineKeyboardBuilder()

    if user_is_following_podcast:
        # kbd.button(text="Unfollow", callback_data=UnfollowCallbackData(podcast_id=podcast.db_object.id))
        kbd.button(text="Unfollow", callback_data="todo")
    else:
        # kbd.button(text="Follow", callback_data=FollowCallbackData(podcast_id=podcast.db_object.id))
        kbd.button(text="Follow", callback_data="todo")

    if podcast.db_object.meta.link:
        kbd.button(text="Podcast website", url=podcast.db_object.meta.link)

    return kbd.as_markup()


class FindView(View):
    async def handle_entrypoint(self, event: CallbackQuery, data: dict[str, typing.Any] | None = None) -> None:
        state: FSMContext = data["state"]

        text = "In your next message, please send me a podcast title you want to find."
        markup = _build_reply_markup()

        await state.set_state(BotState.FIND)

        await event.message.edit_text(text, reply_markup=markup)
        # await answer_entrypoint_event(event, data, message_text=text, query_answer_text=text, reply_markup=markup)

    async def handle_state(self, message: Message, data: dict[str, typing.Any]) -> None:
        state: FSMContext = data["state"]
        bot: Bot = data["bot"]
        user: User = data["user"]

        await state.clear()

        if len(message.text) > 50:  # todo: magic number
            await message.answer("The search query is too long.", reply_markup=_build_result_reply_markup())
            return

        headline_message = await message.answer("🔎 Searching for the podcast...")

        podcasts = await search_podcasts(message.text)
        podcasts_len = len(podcasts)
        if podcasts_len == 0:
            await headline_message.edit_text(
                "No podcasts were found matching your search query. Please try adjusting your keywords.",
                reply_markup=_build_result_reply_markup(),
            )
            return

        await headline_message.edit_text("📨 Sending results to you, please wait a moment...")

        for i, podcast in enumerate(podcasts):
            text = f"{i + 1}/{podcasts_len} {bold(podcast.db_object.meta.title)}\n"

            if podcast.db_object.meta.description:
                text += f"{blockquote(podcast.db_object.meta.description, expandable=True)}\n"

            markup = _build_podcast_card_reply_markup(podcast, user.is_following_podcast(podcast))

            if podcast.db_object.meta.cover_url:
                await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)  # Todo: cache telegram_file_ids

                photo = URLInputFile(podcast.db_object.meta.cover_url)
                await message.answer_photo(
                    photo,
                    caption=text,
                    # link_preview_options=LinkPreviewOptions(
                    #     url=podcast.db_object.meta.link,
                    #     prefer_small_media=True,
                    # ),
                    reply_markup=markup,
                )
            else:
                await message.answer(
                    text,
                    link_preview_options=LinkPreviewOptions(
                        url=podcast.db_object.meta.link,
                        prefer_small_media=True,
                    ),
                    reply_markup=markup,
                )

        await headline_message.edit_text("✨ Here is what I have found:")

        await message.answer(
            "Feel free to use inline buttons to follow podcasts I found. Can I do anything else for you?",
            reply_markup=_build_result_reply_markup(),
        )
