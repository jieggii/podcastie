def link(child: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{child}</a>'
    return child


def code(child: str) -> str:
    return f"<code>{child}</code>"


def bold(child: str) -> str:
    return f"<b>{child}</b>"


def italic(child: str) -> str:
    return f"<i>{child}</i>"


def blockquote(child: str, expandable: bool = False) -> str:
    if expandable:
        return f"<blockquote expandable>{child}</blockquote>"
    return f"<blockquote>{child}</blockquote>"
