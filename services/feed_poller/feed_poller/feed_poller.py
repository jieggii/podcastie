import asyncio
import time
from asyncio import Queue

import aiohttp
import podcastie_rss
import structlog
from podcastie_core.podcast import generate_podcast_title_slug, is_valid_podcast_title
from podcastie_core.service import all_podcasts, podcast_followers
from podcastie_database.models.podcast import PodcastCheckModel, PodcastMetaModel
from podcastie_rss import Episode
from structlog import contextvars
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, wait_exponential

from feed_poller import episode_broadcaster


def _update_podcast_meta(old_meta: PodcastMetaModel, title: str, description: str, link: str, cover_url: str) -> bool:
    changed = False

    if old_meta.title != title and is_valid_podcast_title(title):
        old_meta.title = title
        old_meta.title_slug = generate_podcast_title_slug(title)
        changed = True

    if old_meta.description != description:
        old_meta.description = description
        changed = True

    if old_meta.link != link:
        old_meta.link = link
        changed = True

    if old_meta.cover_url != cover_url:
        old_meta.cover_url = cover_url
        changed = True

    return changed


class FeedPoller:
    _episodes_queue: Queue[Episode]
    _interval: int

    def __init__(self, episodes_queue: Queue[Episode], interval: int):
        self._episodes_queue = episodes_queue
        self._interval = interval

    async def poll_feeds(self) -> None:
        log: structlog.stdlib.BoundLogger = structlog.get_logger(task=self.__class__.__name__)

        while True:
            for podcast in await all_podcasts():
                with contextvars.bound_contextvars(podcast=podcast.document.meta.title):
                    # check if there are any followers:
                    followers = await podcast_followers(podcast)
                    if not followers:
                        # todo: delete podcasts that does not have followers
                        # for SOME amount of time
                        log.info("skipping podcast: it has no followers")
                        continue

                    # fetch podcast RSS feed:
                    feed: podcastie_rss.Feed | None = None
                    try:
                        async for attempt in AsyncRetrying(
                            retry=retry_if_exception_type(aiohttp.ClientConnectorError), wait=wait_exponential(max=60)
                        ):
                            with attempt:
                                feed = await podcastie_rss.fetch_feed(podcast.document.feed_url)
                    except podcastie_rss.FeedError as e:
                        log.bind(e=e).warning("skipping podcast: feed error when attempting to fetch feed")
                        continue
                    except RetryError:
                        log.exception("skipping podcast: retrying error")
                        continue
                    except Exception:
                        log.exception("skipping podcast: unexpected exception while attempting to fetch feed")
                        continue
                    finally:
                        # update information about latest podcast check:
                        podcast.document.check = PodcastCheckModel(timestamp=int(time.time()), success=bool(feed))
                        await podcast.save_changes()

                    # update podcast metadata if it has changed:
                    meta_changed = _update_podcast_meta(
                        podcast.document.meta,
                        title=feed.title,
                        description=feed.description,
                        link=feed.link,
                        cover_url=feed.cover_url,
                    )
                    if meta_changed:
                        await podcast.save_changes()

                    # skip podcast if it does not have any episodes:
                    if not feed.latest_episode:
                        log.debug("skipping podcast: it has no episodes")
                        continue

                    if (podcast.document.latest_episode_publication_timestamp is None) or (
                        feed.latest_episode.published > podcast.document.latest_episode_publication_timestamp
                    ):
                        with contextvars.bound_contextvars(episode=feed.latest_episode.title):
                            log.info("a new episode is out")

                            # update latest episode timestamp in the database:
                            podcast.document.latest_episode_publication_timestamp = feed.latest_episode.published
                            await podcast.save_changes()

                            # skip episode if it does not contain title or audio file:
                            if not feed.latest_episode.title or not feed.latest_episode.audio_file:
                                log.info("skipping episode: it does not contain title or audio")
                                continue

                            log.info("sending episode for broadcasting")
                            episode = episode_broadcaster.Episode(
                                recipients=followers,
                                title=feed.latest_episode.title,
                                audio=feed.latest_episode.audio_file,
                                published_by=podcast,
                                link=feed.latest_episode.link,
                                description=feed.latest_episode.description,
                            )
                            await self._episodes_queue.put(episode)

            log.info(f"task is sleeping for {self._interval} sec")
            await asyncio.sleep(self._interval)
