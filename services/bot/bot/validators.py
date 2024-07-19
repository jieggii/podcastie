import re

FEED_URL_REGEX = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)

PPID_REGEX = re.compile(r".{1,40}\#\d{4}")  # e.g: thejoeroganexperience#4951


def is_feed_url(string: str) -> bool:
    return bool(FEED_URL_REGEX.fullmatch(string))


def is_ppid(string: str) -> bool:
    return bool(PPID_REGEX.fullmatch(string))
