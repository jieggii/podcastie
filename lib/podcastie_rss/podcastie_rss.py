import io
import typing
from dataclasses import dataclass

import aiohttp
import podcastparser

_SUPPORTED_ENCLOSURE_MIME_TYPES = {"audio/mp3", "audio/mpeg"}  # todo: expand to supported by Telegram as we don't need to compress audio anymore


class FeedReadError(Exception):
    pass

class FeedParseError(Exception):
    pass

class FeedValidateError(Exception):
    pass


@dataclass
class AudioFile:
    url: str
    size: int  # size in bytes


@dataclass
class Episode:
    published: int

    title: str | None
    description: str | None
    link: str | None
    audio_file: AudioFile | None


@dataclass
class Feed:
    title: str

    description: str | None
    link: str | None
    cover_url: str | None
    latest_episode: Episode | None


async def _fetch_feed(url: str, *, max_episodes: int) -> dict[str, typing.Any]:
    # todo: use a single session.
    try:
        async with aiohttp.request("GET", url) as response:
            response.raise_for_status()
            content = await response.text()
            return podcastparser.parse(url, io.StringIO(content), max_episodes)

    except aiohttp.ClientError as e:
        raise FeedReadError("failed to read feed") from e
    except podcastparser.FeedParseError as e:
        raise FeedParseError("failed to parse feed") from e

async def fetch_feed(url: str) -> Feed:
    """Fetches feed by RSS feed URL."""
    feed = await _fetch_feed(url, max_episodes=1)

    # parse and validate title (it's required):
    title: str | None = feed.get("title")
    if not title:
        raise FeedValidateError("feed does not contain title")

    # parse podcast description (it's optional):
    description: str | None = feed.get("description")  # todo: check if there are any other fields containing description

    # parse podcast link (it's optional):
    link: str | None = feed.get("link")

    # parse podcast cover URL (it's optional)
    cover_url: str | None = feed.get("cover_url")

    # parse latest podcast episode (it's optional):
    latest_episode: Episode | None = None

    raw_episodes: list[dict[str, typing.Any]] | None = feed.get("episodes")
    if raw_episodes:
        raw_episode: dict[str, typing.Any] = raw_episodes[0]

        # get publication date (it's required, episode will be omitted if it does not contain publication date):
        ep_published: int | None = raw_episode.get("published")
        if ep_published:
            # parse episode title (it's optional) (should it be required?):
            ep_title: str | None = raw_episode.get("title")

            # parse episode link (it's optional):
            ep_link: str | None = raw_episode.get("link")

            # parse episode description (it's optional):
            ep_description: str | None = raw_episode.get("description")

            # parse episode audio file (it's optional):
            ep_audio_file: AudioFile | None = None
            enclosures: list[dict[str, typing.Any]] | None = raw_episode.get("enclosures")
            if enclosures:
                enclosure = enclosures[0]  # use the first enclosure

                # parse file URL (it's required):
                file_url: str | None = enclosure.get("url")

                # parse file size (it's required):
                file_size: int | None = enclosure.get("file_size")

                # parse file mime type (it's required):
                file_mime_type: str | None = enclosure.get("mime_type")

                if file_url and file_size and (file_mime_type in _SUPPORTED_ENCLOSURE_MIME_TYPES):
                    ep_audio_file = AudioFile(url=file_url, size=file_size)

            latest_episode = Episode(
                published=ep_published,
                title=ep_title,
                description=ep_description,
                link=ep_link,
                audio_file=ep_audio_file,
            )

    return Feed(
        title=title,
        description=description,
        link=link,
        cover_url=cover_url,
        latest_episode=latest_episode,
    )
