from dataclasses import dataclass

import podcastie_rss
from podcastie_core.podcast import Podcast
from podcastie_core.user import User


@dataclass
class BroadcastableEpisode:
    recipients: list[User]  # episode recipients
    episode: podcastie_rss.Episode  # episode itself
    published_by: Podcast  # episode publisher
