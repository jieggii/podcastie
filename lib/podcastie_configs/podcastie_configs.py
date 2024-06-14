from typing import NoReturn


def get_value(value: str | None, value_file: str | None) -> str | NoReturn:
    if not (value or value_file):
        raise ValueError("value and value_file are both None")
    if value and value_file:
        raise ValueError(f"value and value_file are both not None")

    if value:
        return value

    with open(value_file) as file:
        return file.read().rstrip()
