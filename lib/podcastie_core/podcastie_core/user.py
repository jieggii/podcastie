from podcastie_database.models.user_model import UserModel

from .podcast import Podcast


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

    async def subscriptions(self) -> list[Podcast]:
        return [
            await Podcast.from_object_id(object_id)
            for object_id in self._model.following_podcasts
        ]

    async def follow(self, podcast: Podcast) -> None:
        if self.is_following(podcast):
            raise UserFollowsPodcastError("user already follows this podcast")

        self._model.following_podcasts.append(podcast.model.id)
        await self._model.save()

    async def unfollow(self, podcast: Podcast) -> None:
        if not self.is_following(podcast):
            raise UserDoesNotFollowPodcastError("user does not follow podcast")

        self._model.following_podcasts.remove(podcast.model.id)
        await self._model.save()

    def is_following(self, podcast: Podcast) -> bool:
        if podcast.model.id in self._model.following_podcasts:
            return True
        return False
