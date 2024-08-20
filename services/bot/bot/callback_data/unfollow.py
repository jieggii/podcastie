from enum import Enum

from aiogram.filters.callback_data import CallbackData as CallbackData
from beanie import PydanticObjectId

# class ReturnTo(Enum):
#     SUBSCRIPTIONS_LIST = "subs"
#     UNFOLLOW_LIST = "unfollow"
#
#
# class UnfollowCTACallbackData(CallbackData, prefix="unfollow_cta"):
#     pass
#
# class UnfollowPromptCallbackData(CallbackData, prefix="unfollow_prompt"):
#     podcast_id: PydanticObjectId
#     return_to: ReturnTo


class UnfollowCallbackData(CallbackData, prefix="unfollow"):
    podcast_id: PydanticObjectId
