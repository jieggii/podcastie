from beanie import PydanticObjectId
from beanie.operators import Text
from podcastie_database.models.podcast import Podcast as _PodcastDatabaseModel

import podcastie_rss


class PodcastNotFoundError(Exception):
    pass

class PodcastFeedError(Exception):
    pass


class Podcast:
    db_object: _PodcastDatabaseModel

    def __init__(self, db_object: _PodcastDatabaseModel):
        self.db_object = db_object

    @classmethod
    async def from_object_id(cls, object_id: PydanticObjectId):
        podcast = await _PodcastDatabaseModel.get(object_id)
        if not podcast:
            raise PodcastNotFoundError("podcast not found")  # todo
        return cls(podcast)

    @classmethod
    async def from_feed_url(cls, feed_url: str):
        podcast = await _PodcastDatabaseModel.find_one(_PodcastDatabaseModel.feed_url == feed_url)
        if not podcast:
            raise PodcastNotFoundError("podcast not found")
        return cls(podcast)

    @classmethod
    async def new_from_feed_url(cls, feed_url: str):
        try:
            feed = await podcastie_rss.fetch_feed(feed_url)
        except (podcastie_rss.FeedReadError, podcastie_rss.FeedParseError, podcastie_rss.FeedValidateError) as e:
            raise PodcastFeedError("failed to fetch podcast feed") from e

        podcast = _PodcastDatabaseModel.from_feed(feed, feed_url)
        await podcast.insert()

        return cls(podcast)

    @classmethod
    async def _from_feed_url_hash_prefix(cls, feed_url_hash_prefix: str):
        podcast = await _PodcastDatabaseModel.find_one(
            _PodcastDatabaseModel.feed_url_hash_prefix == feed_url_hash_prefix
        )
        if not podcast:
            raise PodcastNotFoundError("podcast not found")
        return cls(podcast)

async def search_podcasts(query: str) -> list[Podcast]:
    podcasts = await _PodcastDatabaseModel.find(Text(query)).to_list()
    return [Podcast(p) for p in podcasts]
