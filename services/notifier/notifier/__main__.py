import asyncio
from dataclasses import dataclass

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import URLInputFile
from loguru import logger

import podcastie_configs
import podcastie_database
import podcastie_rss
from podcastie_database.models import Podcast, User

from notifier.env import env


@dataclass
class NewEpisode:
    meta: podcastie_rss.Episode
    telegram_file_id: str | None = None

    def __str__(self) -> str:
        return f"NewEpisode(meta={self.meta}, file_id={self.telegram_file_id})"


async def main() -> None:
    logger.info("initializing database")
    await podcastie_database.init(
        env.Mongo.HOST,
        env.Mongo.PORT,
        podcastie_configs.get_value(env.Mongo.DATABASE, env.Mongo.DATABASE_FILE),
    )

    bot = Bot(
        token=podcastie_configs.get_value(env.Bot.TOKEN, env.Bot.TOKEN_FILE),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    while True:
        logger.info("checking all podcasts for new episodes")

        for podcast in await Podcast.find_all().to_list():
            try:
                feed = await podcastie_rss.fetch_podcast(
                    podcast.feed_url, max_episodes=10
                )
            except podcastie_rss.FeedParseError as e:
                logger.error(f"could not parse podcast feed {podcast=}, {e=}")
                continue
            except Exception as e:
                logger.error(f"could not fetch podcast feed {podcast=}, {e=}")
                continue

            # update stored podcast metadata if it has been updated in the RSS feed:
            update_podcast_meta: bool = False

            if podcast.title != feed.title:
                update_podcast_meta = True
                podcast.title = feed.title
                logger.info(
                    f'got new podcast title: "{podcast.title}" -> "{feed.title}", {podcast=}'
                )

            if podcast.link != feed.link:
                update_podcast_meta = True
                podcast.link = feed.link
                logger.info(
                    f'got new podcast link: "{podcast.link}" -> "{feed.link}", {podcast=}'
                )

            if update_podcast_meta:
                await podcast.save()
                logger.info(f"saved podcast with updated meta {podcast=}")

            # search for new episodes:
            new_episodes: list[NewEpisode] = []
            if feed.episodes:
                for episode in feed.episodes:
                    if episode.publication_date > podcast.latest_episode_date:
                        new_episodes.append(
                            NewEpisode(meta=episode),
                        )
                        continue
                    break

            new_episodes.append(
                NewEpisode(meta=feed.episodes[0])
            )  # this is for debug, remove in prod!
            logger.debug(f"{podcast=} has {len(new_episodes)} new episodes")

            # send missed episodes of the podcast to all subscribers:
            if new_episodes:
                podcast.latest_episode_date = new_episodes[0].meta.publication_date

                users = await User.find(User.following_podcasts == podcast.id).to_list()
                for user in users:
                    for episode in new_episodes:
                        try:
                            await bot.send_message(
                                user.user_id,
                                f"<a href='{episode.meta.file_url}'>A new episode</a> of <a href='{podcast.link}'>{podcast.title}</a> is out!\n"
                                f"\n"
                                f"{episode.meta.description}",
                            )

                            if not episode.telegram_file_id:
                                #  upload file to the Telegram server and cache its file_id:

                                logger.info(
                                    f"start uploading new episode to Telegram and sending it to the user {episode=}, {user=}"
                                )

                                file = URLInputFile(
                                    episode.meta.file_url,
                                    filename=None,  # todo
                                    timeout=120,
                                )
                                message = await bot.send_audio(
                                    user.user_id,
                                    audio=file,
                                    title=episode.meta.title,
                                    performer=podcast.title,
                                    thumbnail=None,  # todo: include thumbnail
                                )
                                episode.telegram_file_id = message.audio.file_id

                            else:  # otherwise send episode audio by its file id if cached:
                                logger.info(
                                    f"sending a new episode to user {episode=}, {user=}"
                                )
                                await bot.send_audio(
                                    user.user_id,
                                    audio=episode.telegram_file_id,
                                    title=episode.meta.title,
                                    performer=podcast.title,
                                    thumbnail=None,  # todo: include thumbnail
                                )

                            logger.info(
                                f"successfully sent a new episode of {podcast=} to {user=}"
                            )
                        except Exception as e:
                            logger.error(
                                f"failed to send a new episode of podcast to user {podcast=} {user=}, {e}"
                            )
        logger.info(f"sleeping for {env.Notifier.PERIOD} seconds")
        await asyncio.sleep(env.Notifier.PERIOD)


if __name__ == "__main__":
    asyncio.run(main())
