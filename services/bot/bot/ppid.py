# NOTE: PPID stands for Podcastie Podcast ID
import random


def generate_ppid(podcast_title: str) -> str:
    ppid = podcast_title.lower().strip()
    ppid = "".join(ppid.split())
    ppid = ppid[:15]
    ppid = f"{ppid}#{random.randint(1000, 9999)}"
    return ppid
