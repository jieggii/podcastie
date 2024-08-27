from beanie.odm.operators.find.evaluation import Text
from podcastie_database.models.podcast import PodcastDocument
from podcastie_database.models.user import UserDocument

from podcastie_core.podcast import Podcast
from podcastie_core.user import User, UserDoesNotFollowPodcastError, UserFollowsPodcastError


async def follow_podcast(user: User, podcast: Podcast) -> None:
    if user_is_following_podcast(user, podcast):
        raise UserFollowsPodcastError("user is following the provided podcast")

    user.document.subscriptions.append(podcast.document.id)
    await user.save_changes()


async def unfollow_podcast(user: User, podcast: Podcast) -> None:
    if not user_is_following_podcast(user, podcast):
        raise UserDoesNotFollowPodcastError("user is not following the provided podcast")

    user.document.subscriptions.remove(podcast.document.id)
    await user.save_changes()


def user_is_following_podcast(user: User, podcast: Podcast) -> bool:
    if podcast.document.id in user.document.subscriptions:
        return True
    return False


async def user_subscriptions(user: User) -> list[Podcast]:
    return [await Podcast.from_object_id(object_id) for object_id in user.document.subscriptions]


async def podcast_followers(podcast: Podcast) -> list[User]:
    models = await UserDocument.find(UserDocument.subscriptions == podcast.document.id).to_list()
    return [User(model) for model in models]


async def search_podcasts(query: str) -> list[Podcast]:
    models = await PodcastDocument.find(Text(query)).to_list()
    return [Podcast(model) for model in models]


async def all_podcasts() -> list[Podcast]:
    # todo: async iterable
    models = await PodcastDocument.find().to_list()
    return [Podcast(model) for model in models]
