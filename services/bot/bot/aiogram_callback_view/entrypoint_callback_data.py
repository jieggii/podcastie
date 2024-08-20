from aiogram.filters.callback_data import CallbackData


class EntrypointCallbackData(CallbackData, prefix=""):
    edit_current_message: bool = True
    clear_state: bool = False
    remove_current_markup: bool = False
