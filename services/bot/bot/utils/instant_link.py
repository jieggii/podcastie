from base64 import urlsafe_b64encode

_FEED_URL_HASH_PREFIX_LEN = 8


def build_instant_link(bot_username: str, podcast_feed_url_hash_prefix: str) -> str:
    if len(podcast_feed_url_hash_prefix) != _FEED_URL_HASH_PREFIX_LEN:
        raise ValueError(
            f"length of podcast_feed_url_hash_prefix must be {_FEED_URL_HASH_PREFIX_LEN}"
        )

    payload = urlsafe_b64encode(podcast_feed_url_hash_prefix.encode()).decode()
    return f"https://t.me/{bot_username}?start={payload}"
