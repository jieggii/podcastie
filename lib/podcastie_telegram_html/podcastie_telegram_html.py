def link(text: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{text}</a>'
    return text

def code(text: str) -> str:
    return f"<code>{text}</code>"
