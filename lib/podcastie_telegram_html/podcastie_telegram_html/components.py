def footer(items: list[str]) -> str:
    return " • ".join(items)


def optional(text: str | None) -> str:
    return text if text else ""
