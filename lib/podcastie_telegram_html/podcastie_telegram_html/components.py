from base64 import urlsafe_b64encode

from . import tags

def footer(items: list[str]) -> str:
    return " • ".join(items)


def optional(child: str | None) -> str:
    return child if child else ""

def start_bot_link(child: str, bot_username: str, payload: str, encode_payload: bool = False) -> str:
    if encode_payload:
        payload = urlsafe_b64encode(payload.encode()).decode()
    return tags.link(child, f"https://t.me/{bot_username}?start={payload}")
