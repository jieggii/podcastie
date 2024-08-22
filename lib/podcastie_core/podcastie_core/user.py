from podcastie_database.models.user_model import UserModel

class UserNotFoundError(Exception):
    pass


class UserFollowsPodcastError(Exception):
    """User already follows podcast"""

    pass


class UserDoesNotFollowPodcastError(Exception):
    pass


class User:
    _model: UserModel

    def __init__(self, model: UserModel):
        self._model = model

    @property
    def model(self) -> UserModel:
        return self._model

    @classmethod
    async def from_user_id(cls, user_id: int):
        user = await UserModel.find_one(UserModel.user_id == user_id)
        if not user:
            raise UserNotFoundError("user not found")

        return cls(user)

    @classmethod
    async def new_from_user_id(cls, user_id: int):
        user = UserModel(user_id=user_id)
        await user.insert()

        return cls(user)
