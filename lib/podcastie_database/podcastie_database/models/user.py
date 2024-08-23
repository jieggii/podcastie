from beanie import Document, PydanticObjectId


class UserDocument(Document):
    user_id: int
    subscriptions: list[PydanticObjectId] = []

    class Settings:
        name = "users"
