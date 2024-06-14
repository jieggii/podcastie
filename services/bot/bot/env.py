from os import getenv

BOT_TOKEN: str | None = getenv("BOT_TOKEN")
BOT_TOKEN_FILE: str | None = getenv("BOT_TOKEN_FILE")

MONGO_HOST: str | None = getenv("MONGO_HOST")
MONGO_PORT: int = int(getenv("MONGO_PORT"))
MONGO_DATABASE: str | None = getenv("MONGO_DATABASE")
MONGO_DATABASE_FILE: str | None = getenv("MONGO_DATABASE_FILE")
