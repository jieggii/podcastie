from dataclasses import dataclass

import podcastie_rss
from podcastie_core.podcast import Podcast
from podcastie_core.user import User


@dataclass
class Episode:
    recipients: list[User]

    title: str
    audio: podcastie_rss.AudioFile
    published_by: Podcast

    link: str | None
    description: str | None

    audio_telegram_file_id: str | None = None  # Telegram file_id of the audio file
