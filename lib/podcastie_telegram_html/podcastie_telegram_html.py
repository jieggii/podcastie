def link(text: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{text}</a>'
    return text


def code(text: str) -> str:
    return f"<code>{text}</code>"

def bold(text: str) -> str:
    return f"<b>{text}</b>"

def optional(text: str | None) -> str:
    return text if text else ""

def footer(items: list[str]) -> str:
    return " • ".join(items)
