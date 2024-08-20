from beanie import PydanticObjectId
from bot.aiogram_callback_view.entrypoint_callback_data import EntrypointCallbackData


class MenuViewEntrypointCallbackData(EntrypointCallbackData, prefix="menu"):
    pass

class FindViewEntrypointCallbackData(EntrypointCallbackData, prefix="find"):
    pass

class ImportViewEntrypointCallbackData(EntrypointCallbackData, prefix="import"):
    pass


class ExportViewEntrypointCallbackData(EntrypointCallbackData, prefix="export"):
    pass

class SubscriptionsViewEntrypointCallbackData(EntrypointCallbackData, prefix="subs"):
    pass


class PodcastViewEntrypointCallbackData(EntrypointCallbackData, prefix="podcast"):
    podcast_id: PydanticObjectId


class ShareViewEntrypointCallbackData(EntrypointCallbackData, prefix="share"):
    podcast_id: PydanticObjectId


