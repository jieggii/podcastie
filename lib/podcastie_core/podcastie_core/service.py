from beanie.odm.operators.find.evaluation import Text
from podcastie_core.user import UserFollowsPodcastError, UserDoesNotFollowPodcastError
from podcastie_core.podcast import Podcast
from podcastie_core.user import User
from podcastie_database.models.podcast_model import PodcastModel
from podcastie_database.models.user_model import UserModel


async def follow_podcast(user: User, podcast: Podcast) -> None:
    if user_is_following_podcast(user, podcast):
        raise UserFollowsPodcastError("user is following the provided podcast")

    user.model.following_podcasts.append(podcast.model.id)
    await user.model.save()


async def unfollow_podcast(user: User, podcast: Podcast) -> None:
    if not user_is_following_podcast(user, podcast):
        raise UserDoesNotFollowPodcastError("user is not following the provided podcast")

    user.model.following_podcasts.remove(podcast.model.id)
    await user.model.save()


def user_is_following_podcast(user: User, podcast: Podcast) -> bool:
    if podcast.model.id in user.model.following_podcasts:
        return True
    return False


async def user_subscriptions(user: User) -> list[Podcast]:
    return [
        await Podcast.from_object_id(object_id)
        for object_id in user.model.following_podcasts
    ]

async def podcast_followers(podcast: Podcast) -> list[User]:
    models = await UserModel.find(UserModel.following_podcasts == podcast.model.id).to_list()
    return [User(model) for model in models]


async def search_podcasts(query: str) -> list[Podcast]:
    models = await PodcastModel.find(Text(query)).to_list()
    return [Podcast(model) for model in models]


async def all_podcasts() -> list[Podcast]:
    models = await PodcastModel.find().to_list()
    return [Podcast(model) for model in models]
