import typing

from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from podcastie_telegram_html.tags import blockquote, bold

from bot.aiogram_view.view import View
from bot.callback_data.entrypoints import (
    SearchResultAction,
    SearchResultViewEntrypointCallbackData,
)
from bot.core.podcast import Podcast, PodcastNotFoundError
from bot.core.user import User, UserDoesNotFollowPodcastError, UserFollowsPodcastError


class SearchResultView(View):
    @staticmethod
    def _build_follow_keyboard(
        podcast_id: PydanticObjectId, podcast_link: str | None
    ) -> InlineKeyboardMarkup:
        kbd = InlineKeyboardBuilder()
        kbd.button(
            text="Follow",
            callback_data=SearchResultViewEntrypointCallbackData(
                podcast_id=podcast_id,
                action=SearchResultAction.follow,
            ),
        )
        if podcast_link:
            kbd.button(text="Podcast website", url=podcast_link)

        return kbd.as_markup()

    @staticmethod
    def _build_unfollow_keyboard(
        podcast_id: PydanticObjectId, podcast_link: str | None
    ) -> InlineKeyboardMarkup:
        kbd = InlineKeyboardBuilder()
        kbd.button(
            text="Unfollow",
            callback_data=SearchResultViewEntrypointCallbackData(
                podcast_id=podcast_id, action=SearchResultAction.unfollow
            ),
        )
        if podcast_link:
            kbd.button(text="Podcast website", url=podcast_link)

        return kbd.as_markup()

    async def handle_entrypoint(
        self, event: CallbackQuery | Message, data: dict[str, typing.Any]
    ) -> None:
        callback_data: SearchResultViewEntrypointCallbackData = data["callback_data"]
        user: User = data["user"]

        try:
            podcast = await Podcast.from_object_id(callback_data.podcast_id)
        except PodcastNotFoundError:
            await event.answer("⚠️ Podcast not found.", show_alert=True)
            return

        match callback_data.action:
            case SearchResultAction.follow:
                try:
                    await user.follow_podcast(podcast)
                    await event.message.edit_reply_markup(
                        reply_markup=self._build_unfollow_keyboard(
                            podcast.db_object.id, podcast.db_object.meta.link
                        )
                    )
                    await event.answer(
                        f"🔔 Successfully followed {podcast.db_object.meta.title}."
                    )
                except UserFollowsPodcastError:
                    await event.message.edit_reply_markup(
                        reply_markup=self._build_unfollow_keyboard(
                            podcast.db_object.id, podcast.db_object.meta.link
                        )
                    )
                    await event.answer(
                        f"🔔 You already follow {podcast.db_object.meta.title}."
                    )

            case SearchResultAction.unfollow:
                try:
                    await user.unfollow_podcast(podcast)
                    await event.message.edit_reply_markup(
                        reply_markup=self._build_follow_keyboard(
                            podcast.db_object.id, podcast.db_object.meta.link
                        )
                    )
                    await event.answer(
                        f"🔕 Successfully unfollowed from {podcast.db_object.meta.title}."
                    )
                except UserDoesNotFollowPodcastError:
                    await event.message.edit_reply_markup(
                        reply_markup=self._build_follow_keyboard(
                            podcast.db_object.id, podcast.db_object.meta.link
                        )
                    )
                    await event.answer(
                        f"🔕 You don't follow {podcast.db_object.meta.title}."
                    )

            case SearchResultAction.send:
                if not isinstance(event, Message):
                    raise ValueError("expected Message event")
                if not callback_data.result_number:
                    raise ValueError("todo")
                if not callback_data.total_results:
                    raise ValueError("todo")

                bot: Bot = data["bot"]

                text = f"{callback_data.result_number}/{callback_data.total_results} {bold(podcast.db_object.meta.title)}\n"

                if podcast.db_object.meta.description:
                    text += f"{blockquote(podcast.db_object.meta.description, expandable=True)}\n"

                markup: InlineKeyboardMarkup
                if user.is_following_podcast(podcast):
                    markup = self._build_unfollow_keyboard(
                        podcast.db_object.id, podcast.db_object.meta.link
                    )
                else:
                    markup = self._build_follow_keyboard(
                        podcast.db_object.id, podcast.db_object.meta.link
                    )

                if podcast.db_object.meta.cover_url:
                    await bot.send_chat_action(
                        event.chat.id, ChatAction.UPLOAD_PHOTO
                    )  # Todo: cache telegram_file_ids

                    photo = URLInputFile(podcast.db_object.meta.cover_url)
                    await event.answer_photo(photo, caption=text, reply_markup=markup)
                else:
                    await event.answer(text, reply_markup=markup)

            case _:
                raise ValueError("unexpected action")
