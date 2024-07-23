_ESCAPE_TOKENS = {
    ">": "&gt;",
    "<": "&lt;",
    "&": "&amp;"
}


def escape(text: str) -> str:
    """
    TODO: escape only invalid Telegram tags, leave valid tags (e.g. <a href="smth">smth</a>) as is.
    https://core.telegram.org/bots/api#html-style
    """
    global _ESCAPE_TOKENS
    for old, new in _ESCAPE_TOKENS.items():
        text = text.replace(old, new)
    return text
