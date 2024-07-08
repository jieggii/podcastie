from typing import NoReturn

from betterconf import Config, compose_field, field
from betterconf.caster import to_int


def get_value(value: str | None, value_file: str | None) -> str | NoReturn:
    if not (value or value_file):
        raise ValueError("value and value file are both None")
    if value and value_file:
        raise ValueError(f"value and value file both are not None")

    if value:
        return value

    with open(value_file) as file:
        return file.read().rstrip()


class Env(Config):
    class Bot(Config):
        _TOKEN = field("BOT_TOKEN", default=None)
        _TOKEN_FILE = field("BOT_TOKEN_FILE", default=None)
        TOKEN: str = compose_field(
            _TOKEN,
            _TOKEN_FILE,
            lambda token, token_file: get_value(token, token_file),
        )

    class Notifier(Config):
        POLL_INTERVAL = field("NOTIFIER_POLL_INTERVAL", caster=to_int)

    class Mongo(Config):
        HOST = field("MONGO_HOST")
        PORT = field("MONGO_PORT", caster=to_int)

        _DATABASE = field("MONGO_DATABASE", default=None)
        _DATABASE_FILE = field("MONGO_DATABASE_FILE", default=None)
        DATABASE: str = compose_field(
            _DATABASE, _DATABASE_FILE, lambda database, database_file: get_value(database, database_file)
        )


env = Env()
