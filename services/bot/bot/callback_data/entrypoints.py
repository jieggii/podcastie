from enum import Enum

from beanie import PydanticObjectId

from bot.aiogram_view.entrypoint_callback_data import EntrypointCallbackData


class MenuViewEntrypointCallbackData(EntrypointCallbackData, prefix="menu"):
    pass


class FindViewEntrypointCallbackData(EntrypointCallbackData, prefix="find"):
    pass


class SearchResultAction(Enum):
    follow = "follow"
    unfollow = "unfollow"
    send = "send"


class SearchResultViewEntrypointCallbackData(
    EntrypointCallbackData, prefix="search_result"
):
    podcast_id: PydanticObjectId
    action: SearchResultAction
    result_number: int | None = None
    total_results: int | None = None


class ImportViewEntrypointCallbackData(EntrypointCallbackData, prefix="import"):
    pass


class ExportViewEntrypointCallbackData(EntrypointCallbackData, prefix="export"):
    pass


class SubscriptionsViewEntrypointCallbackData(EntrypointCallbackData, prefix="subs"):
    unfollow_podcast_id: PydanticObjectId | None = (
        None  # podcast_id to unfollow before displaying the view
    )


class PodcastViewEntrypointCallbackData(EntrypointCallbackData, prefix="podcast"):
    podcast_id: PydanticObjectId


class ShareViewEntrypointCallbackData(EntrypointCallbackData, prefix="share"):
    podcast_id: PydanticObjectId


class UnfollowViewEntrypointCallbackData(EntrypointCallbackData, prefix="unfollow"):
    podcast_id: PydanticObjectId
