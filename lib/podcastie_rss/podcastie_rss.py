import datetime
import io
import typing
from dataclasses import dataclass, field

import aiohttp
import podcastparser


class FeedParseError(podcastparser.FeedParseError):
    pass


@dataclass
class Episode:
    title: str | None
    description: str | None
    link: str | None
    publication_date: datetime.datetime | None
    file_url: str | None


@dataclass
class Podcast:
    title: str | None
    link: str | None
    cover_url: str | None

    episodes: list[Episode]


async def _fetch_podcast_feed(url: str, max_episodes: int) -> dict[str, typing.Any]:
    async with aiohttp.request("GET", url) as response:
        content = await response.text()
        return podcastparser.parse(url, io.StringIO(content), max_episodes)


async def fetch_podcast(url: str, max_episodes: int = 0) -> Podcast:
    feed = await _fetch_podcast_feed(url, max_episodes)

    podcast = Podcast(
        title=feed.get("title"),
        link=feed.get("link"),
        cover_url=feed.get("cover_url"),
        episodes=[],
    )

    # parse episodes:
    raw_episodes = feed.get("episodes")
    if raw_episodes is None:
        return podcast

    for raw_episode in raw_episodes:
        raw_episode: dict[str, typing.Any]

        # parse audio file URL:
        file_url: None | str = None
        enclosures: None | list[dict[str, typing.Any]] = raw_episode.get("enclosures")
        if enclosures:
            file_url = enclosures[0].get("url")

        # parse publication date:
        publication_date: None | datetime.datetime = None
        published: None | int = raw_episode.get("published")
        if published:
            publication_date = datetime.datetime.fromtimestamp(published)

        episode = Episode(
            title=raw_episode.get("title"),
            description=raw_episode.get("description"),
            link=raw_episode.get("link"),
            publication_date=publication_date,
            file_url=file_url,
        )
        podcast.episodes.append(episode)

    return podcast
