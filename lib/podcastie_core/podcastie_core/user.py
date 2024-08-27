from podcastie_database.models.user import UserDocument


class UserNotFoundError(Exception):
    pass


class UserFollowsPodcastError(Exception):
    """User already follows podcast"""

    pass


class UserDoesNotFollowPodcastError(Exception):
    pass


class User:
    _document: UserDocument

    def __init__(self, document: UserDocument):
        self._document = document

    @property
    def document(self) -> UserDocument:
        return self._document

    @classmethod
    async def from_user_id(cls, user_id: int):
        user = await UserDocument.find_one(UserDocument.user_id == user_id)
        if not user:
            raise UserNotFoundError("user not found")

        return cls(user)

    @classmethod
    async def new_from_user_id(cls, user_id: int):
        user = UserDocument(user_id=user_id)
        await user.insert()

        return cls(user)

    async def save_changes(self) -> None:
        await self._document.save()
