from podcastie_database.models.user import User as _UserDatabaseModel
from typing_extensions import AsyncGenerator

from .podcast import Podcast


class UserNotFoundError(Exception):
    pass

class UserFollowsPodcastError(Exception):
    """User already follows podcast"""

    pass


class UserDoesNotFollowPodcastError(Exception):
    pass


class User:
    def __init__(self, db_object: _UserDatabaseModel):
        self._db_object = db_object

    @property
    def db_object(self) -> _UserDatabaseModel:
        return self._db_object

    @classmethod
    async def from_user_id(cls, user_id: int):
        user = await _UserDatabaseModel.find_one(_UserDatabaseModel.user_id == user_id)
        if not user:
            raise UserNotFoundError("user not found")

        return cls(user)

    @classmethod
    async def new_from_user_id(cls, user_id: int):
        user = _UserDatabaseModel(user_id=user_id)
        await user.insert()

        return cls(user)

    async def subscriptions(self) -> list[Podcast]:
        return [
            await Podcast.from_object_id(object_id)
            for object_id in self._db_object.following_podcasts
        ]

    async def follow(self, podcast: Podcast) -> None:
        if self.is_following(podcast):
            raise UserFollowsPodcastError("user already follows this podcast")

        self._db_object.following_podcasts.append(podcast.db_object.id)
        await self._db_object.save()

    async def unfollow(self, podcast: Podcast) -> None:
        if not self.is_following(podcast):
            raise UserDoesNotFollowPodcastError(
                "user does not follow podcast"
            )

        self._db_object.following_podcasts.remove(podcast.db_object.id)
        await self._db_object.save()

    def is_following(self, podcast: Podcast) -> bool:
        if podcast.db_object.id in self._db_object.following_podcasts:
            return True
        return False
