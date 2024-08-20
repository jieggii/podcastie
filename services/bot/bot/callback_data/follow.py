from aiogram.filters.callback_data import CallbackData
from beanie import PydanticObjectId


class FollowCallbackData(CallbackData, prefix="follow"):
    podcast_id: PydanticObjectId
