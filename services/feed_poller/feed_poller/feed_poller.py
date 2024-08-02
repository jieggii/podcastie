import asyncio
import time
from typing import Awaitable, Callable

import aiohttp
import podcastie_rss
import structlog
from podcastie_database.models.podcast import Podcast, PodcastMetaPatch, generate_podcast_title_slug
from podcastie_database.models.user import User
from structlog.contextvars import bind_contextvars, clear_contextvars

from feed_poller import episode_broadcaster
from feed_poller.http_retryer import HTTPRetryer

_EPISODE_CONSUMER_TYPE = Callable[[episode_broadcaster.Episode], Awaitable[None]]


class FeedPoller:
    _interval: int
    _new_episode_consumer: _EPISODE_CONSUMER_TYPE

    _http_retryer: HTTPRetryer

    _task_name = "feed_poller"

    def __init__(self, interval: int, new_episode_consumer: _EPISODE_CONSUMER_TYPE):
        self._interval = interval
        self._new_episode_consumer = new_episode_consumer

        self._http_retryer = HTTPRetryer(interval=1, max_attempts=10)

    async def run(self) -> None:
        log = structlog.getLogger().bind(task=self._task_name)

        while True:
            # get all podcasts stored in the database:
            podcasts = await Podcast.find().to_list()

            for podcast in podcasts:
                bind_contextvars(podcast=podcast.meta.title)

                # check if there are any followers:
                log.info(f"checking if podcast has followers")
                followers = await User.find(User.following_podcasts == podcast.id).to_list()
                if not followers:
                    # todo: delete podcasts that does not have followers
                    # for SOME amount of time
                    log.info("skip podcast as it has no followers")
                    continue

                # try to fetch podcast RSS feed:
                log.info(f"checking podcast RSS feed for new updates")
                feed: podcastie_rss.Feed | None = None
                try:
                    feed = await self._http_retryer.wrap(
                        podcastie_rss.fetch_feed,
                        kwargs={"url": podcast.feed_url},
                        retry_callback=lambda attempt, prev_e: log.warning(
                            "retrying to fetch RSS feed", attempt=attempt, e=prev_e
                        ),
                    )
                except Exception as e:
                    match e:
                        case aiohttp.ClientError():
                            log.warning(
                                f"http client error while attempting to read feed",
                                podcast_title=podcast.meta.title,
                                e=e,
                            )
                        case podcastie_rss.MalformedFeedFormatError():
                            log.warning(f"feed is malformed", podcast_title=podcast.meta.title, e=e)

                        case podcastie_rss.MissingFeedTitleError():
                            log.warning(f"feed did not pass validation", podcast_title=podcast.meta.title, e=e)

                        case _:
                            log.exception(
                                f"unexpected exception while attempting to read feed",
                                podcast_title=podcast.meta.title,
                                e=e,
                            )

                podcast.latest_episode_info.check_ts = int(time.time())
                podcast.latest_episode_info.check_success = bool(feed)
                await podcast.save()

                if feed is None:
                    log.warning("skip podcast as was not able to check its feed")
                    continue

                # update podcast metadata if it has changed:
                podcast_meta_patch: PodcastMetaPatch = {}
                if podcast.meta.title != feed.title:
                    log.info(f"update podcast title", new_title=feed.title)
                    podcast_meta_patch["new_title"] = feed.title
                    podcast_meta_patch["new_title_slug"] = generate_podcast_title_slug(feed.title)

                if podcast.meta.description != feed.description:
                    log.info(f"update podcast description", new_description_len=len(feed.description))
                    podcast_meta_patch["new_description"] = feed.description

                if podcast.meta.link != feed.link:
                    log.info(f"update podcast link", new_link=feed.link)
                    podcast_meta_patch["new_link"] = feed.link

                if podcast.meta.cover_url != feed.cover_url:
                    log.info(f"update podcast cover url", new_cover_url=feed.cover_url)
                    podcast_meta_patch["new_cover_url"] = feed.cover_url

                podcast_meta_patched = podcast.meta.patch(podcast_meta_patch)
                if podcast_meta_patched:
                    await podcast.save()

                # skip podcast if it does not have any episodes:
                if not feed.latest_episode:
                    log.debug(f"skip podcast as it has no episodes")
                    continue

                if (podcast.latest_episode_info.publication_ts is None) or (
                    feed.latest_episode.published > podcast.latest_episode_info.publication_ts
                ):
                    bind_contextvars(episode=feed.latest_episode.title)
                    log.info(f"new episode is out")

                    # update latest episode timestamp in the database:
                    podcast.latest_episode_info.publication_ts = feed.latest_episode.published
                    await podcast.save()

                    # skip episode if it does not contain title or audio file:
                    if not feed.latest_episode.title or not feed.latest_episode.audio_file:
                        log.info("skip episode because it does not contain title or audio")
                        continue

                    log.info("send episode to the BROADCAST queue")
                    episode = episode_broadcaster.Episode(
                        recipient_user_ids=[follower.user_id for follower in followers],
                        title=feed.latest_episode.title,
                        audio=feed.latest_episode.audio_file,
                        podcast=podcast,
                        link=feed.latest_episode.link,
                        description=feed.latest_episode.description,
                    )
                    await self._new_episode_consumer(episode)

                    clear_contextvars()

            clear_contextvars()
            log.info(f"task is sleeping", sleep_sec=self._interval)
            await asyncio.sleep(self._interval)
