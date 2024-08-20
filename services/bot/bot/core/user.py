from podcastie_database.models.user import User as _User
from .podcast import Podcast

class UserFollowsPodcastError(Exception):
    """User already follows podcast"""
    pass

class UserDoesNotFollowPodcastError(Exception):
    pass


class User:
    db_object: _User

    def __init__(self, db_object: _User):
        self.db_object = db_object

    async def get_following_podcasts(self) -> list[Podcast]:
        # todo: yield?
        podcasts: list[Podcast] = []
        for object_id in self.db_object.following_podcasts:
            podcasts.append(await Podcast.from_object_id(object_id))

        return podcasts

    async def follow_podcast(self, podcast: Podcast) -> None:
        if self.is_following_podcast(podcast):
            raise UserFollowsPodcastError("user already follows this podcast")

        self.db_object.following_podcasts.append(podcast.db_object.id)
        await self.db_object.save()

    async def batch_follow_podcasts(self, podcasts: list[Podcast]):
        for podcast in podcasts:
            await self.follow_podcast(podcast)

    async def unfollow_podcast(self, podcast: Podcast) -> None:
        if not self.is_following_podcast(podcast):
            raise UserDoesNotFollowPodcastError("user does not follow this podcast anyway")

        self.db_object.following_podcasts.remove(podcast.db_object.id)
        await self.db_object.save()

    def is_following_podcast(self, podcast: Podcast) -> bool:
        if podcast.db_object.id in self.db_object.following_podcasts:
            return True
        return False
