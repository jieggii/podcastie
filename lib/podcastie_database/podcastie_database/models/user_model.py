from beanie import Document, PydanticObjectId


class UserModel(Document):
    user_id: int
    following_podcasts: list[PydanticObjectId] = []

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return self.__str__()
