import typing

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.aiogram_view.entrypoint_callback_data import EntrypointCallbackData


async def answer_callback_query_entrypoint_event(
    event: CallbackQuery,
    data: dict[str, typing.Any],
    *,
    message_text: str,
    query_answer_text: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    callback_data: EntrypointCallbackData = data["callback_data"]

    if query_answer_text:
        await event.answer(query_answer_text)

    if callback_data.edit_current_message:
        await event.message.edit_text(message_text, reply_markup=reply_markup)
    else:
        await event.message.answer(message_text, reply_markup=reply_markup)


async def answer_entrypoint_event(
    event: Message | CallbackQuery,
    data: dict[str, typing.Any],
    message_text: str | None = None,
    query_answer_text: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if isinstance(event, Message):
        await event.answer(message_text, reply_markup=reply_markup)

    elif isinstance(event, CallbackQuery):
        await answer_callback_query_entrypoint_event(
            event,
            data,
            message_text=message_text,
            query_answer_text=query_answer_text,
            reply_markup=reply_markup,
        )

    else:
        raise ValueError("unexpected event type")
