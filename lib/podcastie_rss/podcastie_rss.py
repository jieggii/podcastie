import datetime
import io
import typing
from dataclasses import dataclass, field

import aiohttp
import podcastparser


class InvalidFeedError(podcastparser.FeedParseError):
    pass


class UntitledPodcastError(Exception):
    pass


@dataclass
class AudioFile:
    url: str
    size: int

    def __str__(self) -> str:
        return f"AudioFile(url={self.url} size={self.size})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class Episode:
    publication_date: datetime.datetime

    title: str | None
    description: str | None
    link: str | None
    audio_file: AudioFile | None


@dataclass
class Podcast:
    title: str
    episodes: list[Episode]

    link: str | None
    cover_url: str | None


async def _fetch_podcast_feed(url: str, max_episodes: int) -> dict[str, typing.Any]:
    async with aiohttp.request("GET", url) as response:
        content = await response.text()
        return podcastparser.parse(url, io.StringIO(content), max_episodes)


async def fetch_podcast(url: str, max_episodes: int = 0) -> Podcast:
    feed = await _fetch_podcast_feed(url, max_episodes)

    # get and validate title (it's required):
    podcast_title: str | None = feed.get("title")
    if not podcast_title:
        raise UntitledPodcastError("podcast does not have title")

    # get list of podcast episodes (they are required, but can be an empty list):
    raw_episodes: list[dict[str, typing.Any]] | None = feed.get("episodes")
    podcast_episodes: list[Episode] = []

    if raw_episodes:
        for raw_episode in raw_episodes:
            # get publication date (it's required, episode will be omitted if it does not contain publication date):
            published: None | int = raw_episode.get("published")
            if published is None:  # skip episodes without publication date
                continue

            ep_publication_date = datetime.datetime.fromtimestamp(published)

            # get episode title (it's optional):
            ep_title: str | None = raw_episode.get("title")

            # get episode description (it's optional):
            ep_description: str | None = raw_episode.get("description")

            # get episode link (it's optional):
            ep_link: str | None = raw_episode.get("link")

            # get audio file (it's optional):
            ep_audio_file: AudioFile | None = None
            enclosures: list[dict[str, typing.Any]] | None = raw_episode.get(
                "enclosures"
            )
            if enclosures:
                print(enclosures)
                # get file URL (it's required):
                file_url: str | None = enclosures[0].get("url")

                # get file size (it's required):
                file_size: int | None = enclosures[0].get("file_size")
                if file_url and file_size:
                    ep_audio_file = AudioFile(url=file_url, size=file_size)

            episode = Episode(
                publication_date=ep_publication_date,
                title=ep_title,
                description=ep_description,
                link=ep_link,
                audio_file=ep_audio_file,
            )
            podcast_episodes.append(episode)

    # get podcast link (it's optional):
    podcast_link: str | None = feed.get("link")

    # get podcast cover URL (it's optional)
    podcast_cover_url: str | None = feed.get("cover_url")

    podcast = Podcast(
        title=podcast_title,
        link=podcast_link,
        cover_url=podcast_cover_url,
        episodes=podcast_episodes,
    )

    return podcast
