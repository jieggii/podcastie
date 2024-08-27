from beanie import Document, PydanticObjectId, Indexed


class UserDocument(Document):
    user_id: Indexed(int, unique=True)
    subscriptions: list[PydanticObjectId] = []

    class Settings:
        name = "users"
