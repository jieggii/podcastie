def link(text: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{text}</a>'
    return text
