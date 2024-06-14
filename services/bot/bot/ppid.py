# NOTE: PPID stands for Podcastie Podcast ID
import random


def generate_ppid(podcast_title: str) -> str:
    return f"ppid:{podcast_title.lower()[:10]}#{random.randint(1000, 9999)}"
