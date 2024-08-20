from beanie import PydanticObjectId
from aiogram.filters.callback_data import CallbackData


class FollowCallbackData(CallbackData, prefix="follow"):
    podcast_id: PydanticObjectId
