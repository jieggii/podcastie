def link(child: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{child}</a>'
    return child


def code(child: str) -> str:
    return f"<code>{child}</code>"


def bold(child: str) -> str:
    return f"<b>{child}</b>"

