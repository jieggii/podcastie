import datetime
import io
import typing
from dataclasses import dataclass

import aiohttp
import podcastparser

_SUPPORTED_ENCLOSURE_MIME_TYPES = ("audio/mp3", "audio/mpeg")


class MalformedFeedFormatError(Exception):
    """Is raised when unable to parse feed as it's content is malformed/not valid."""

    pass


class FeedDidNotPassValidation(Exception):
    """Is raised when feed did not pass validation after parsing it."""

    pass


@dataclass
class AudioFile:
    url: str
    size: int  # size in bytes


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
    try:
        feed = await _fetch_podcast_feed(url, max_episodes)
    except podcastparser.FeedParseError:
        raise MalformedFeedFormatError()

    # get and validate title (it's required):
    podcast_title: str | None = feed.get("title")
    if not podcast_title:
        raise FeedDidNotPassValidation("podcast does not have title")

    # get podcast link (it's optional):
    podcast_link: str | None = feed.get("link")

    # get podcast cover URL (it's optional)
    podcast_cover_url: str | None = feed.get("cover_url")

    # get podcast episodes (they are required, but can be an empty list):
    raw_episodes: list[dict[str, typing.Any]] | None = feed.get("episodes")
    podcast_episodes: list[Episode] = []

    if raw_episodes:
        for raw_episode in raw_episodes:
            # get publication date (it's required, episode will be omitted if it does not contain publication date):
            published: int | None = raw_episode.get("published")
            if published is None:  # skip episodes without publication date
                continue

            ep_publication_date = datetime.datetime.fromtimestamp(published, datetime.UTC)

            # get episode title (it's optional):
            ep_title: str | None = raw_episode.get("title")

            # get episode description (it's optional):
            ep_description: str | None = raw_episode.get("description")

            # get episode link (it's optional):
            ep_link: str | None = raw_episode.get("link")

            # get audio file (it's optional):
            ep_audio_file: AudioFile | None = None
            enclosures: list[dict[str, typing.Any]] | None = raw_episode.get("enclosures")
            if enclosures:
                enclosure = enclosures[0]  # use the first enclosure

                # get file URL (it's required):
                file_url: str | None = enclosure.get("url")

                # get file size (it's required):
                file_size: int | None = enclosure.get("file_size")

                # get file mime type (it's required):
                file_mime_type: str | None = enclosure.get("mime_type")

                if file_url and file_size and (file_mime_type in _SUPPORTED_ENCLOSURE_MIME_TYPES):
                    ep_audio_file = AudioFile(url=file_url, size=file_size)

            episode = Episode(
                publication_date=ep_publication_date,
                title=ep_title,
                description=ep_description,
                link=ep_link,
                audio_file=ep_audio_file,
            )
            podcast_episodes.append(episode)

    podcast = Podcast(
        title=podcast_title,
        link=podcast_link,
        cover_url=podcast_cover_url,
        episodes=podcast_episodes,
    )

    return podcast
