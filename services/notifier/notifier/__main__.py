import asyncio
from dataclasses import dataclass

import podcastie_configs
import podcastie_database
import podcastie_rss
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import URLInputFile
from loguru import logger
from podcastie_database.models import Podcast, User

from notifier.env import env


@dataclass
class NewEpisode:
    meta: podcastie_rss.Episode
    audio_file_telegram_id: str | None = None

    def __str__(self) -> str:
        return f"NewEpisode(meta={self.meta} audio_file_telegram_id={self.audio_file_telegram_id})"


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
            except (
                podcastie_rss.InvalidFeedError,
                podcastie_rss.UntitledPodcastError,
            ) as e:
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
                        # format episode publication date:
                        fmt_ep_publication_date = f"{episode.meta.publication_date.strftime("%d.%m.%Y at %H:%M")}"

                        # format episode title:
                        fmt_ep_title = (
                            episode.meta.title if episode.meta.title else "[no title]"
                        )

                        # format <a> episode title:
                        fmt_ep_a_title = (
                            f'<a href="{episode.meta.link}">{fmt_ep_title}</a>'
                            if episode.meta.link
                            else fmt_ep_title
                        )

                        # format episode description:
                        fmt_ep_description = (
                            episode.meta.description
                            if episode.meta.description
                            else "[empty description]"
                        )

                        fmt_ep_file_download_link = (
                            f'<a href="{episode.meta.audio_file.url}">here</a>'
                            if episode.meta.audio_file
                            else "[not available]"
                        )

                        # format <a> podcast title:
                        fmt_podcast_a_title = (
                            f'<a href="{podcast.link}">{podcast.title}</a>'
                            if podcast.link
                            else podcast.title
                        )

                        # create episode thumbnail image file if available:
                        thumbnail_file: URLInputFile | None = (
                            URLInputFile(feed.cover_url) if feed.cover_url else None
                        )

                        try:
                            # send notification about the new episode containing its meta:
                            logger.info(
                                f"sending text notification about the new episode to user {episode=} {user=}"
                            )
                            await bot.send_message(
                                user.user_id,
                                f"🎉 {fmt_podcast_a_title} has published a new episode - {fmt_ep_a_title}\n"
                                "\n"
                                f"{fmt_ep_description}\n"
                                "\n"
                                f"📅 Episode was published on  {fmt_ep_publication_date}.\n"
                                f"📁 Download episode audio {fmt_ep_file_download_link}.\n",
                            )

                        except Exception as e:
                            logger.info(
                                f"failed to send text notification about the new episode to user, will skip trying sending audio {episode=} {user=} {e=}"
                            )
                            continue

                        try:
                            # send new episode's audio file if it is provided:
                            if not episode.meta.audio_file:
                                logger.info(
                                    f"skip sending audio file of the new episode to the user as there is no audio file provided {episode=} {user=}"
                                )
                                continue

                            if episode.meta.audio_file.size > 5e7:
                                logger.info(
                                    f"skip sending audio file of the new episode to the user as the audio file size exceeds limit {episode=} {user=}"
                                )
                                await bot.send_message(
                                    user.user_id,
                                    "📏 Episode audio file size exceeds Telegram limit (50MB), so I am not sending it to you 😭",
                                )
                                continue

                            # send it through uploading file to Telegram server if no file_id cached for it:
                            if not episode.audio_file_telegram_id:
                                logger.info(
                                    f"start sending the new episode audio file to the user by uploading it to the Telegram server {episode=}, {user=}"
                                )

                                audio_file = URLInputFile(
                                    episode.meta.audio_file.url,
                                    timeout=120,
                                )
                                message = await bot.send_audio(
                                    user.user_id,
                                    audio=audio_file,
                                    title=fmt_ep_title,
                                    performer=podcast.title,
                                    thumbnail=thumbnail_file,
                                )
                                episode.audio_file_telegram_id = message.audio.file_id

                            else:  # otherwise send episode file by its file id:
                                logger.info(
                                    f"sending the new episode to the user by file_id {episode=}, {user=}, {episode.audio_file_telegram_id=}"
                                )
                                await bot.send_audio(
                                    user.user_id,
                                    audio=episode.audio_file_telegram_id,
                                    title=fmt_ep_title,
                                    performer=podcast.title,
                                    thumbnail=thumbnail_file,
                                )

                        except Exception as e:
                            logger.error(
                                f"failed to send audio file of the new episode to user {episode=} {user=}, {e}"
                            )

        logger.info(f"sleeping for {env.Notifier.PERIOD} seconds")
        await asyncio.sleep(env.Notifier.PERIOD)


if __name__ == "__main__":
    asyncio.run(main())
