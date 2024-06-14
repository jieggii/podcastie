from datetime import datetime

from beanie import Document, Link, PydanticObjectId


class Podcast(Document):
    ppid: str
    title: str
    link: str
    feed_url: str
    latest_episode_date: datetime | None = None

    class Settings:
        name = "podcasts"

    def __str__(self) -> str:
        return f"Podcast(id={self.id}, title={self.title}, link={self.link}, feed_url={self.feed_url})"

    def __repr__(self) -> str:
        return self.__str__()


class User(Document):
    user_id: int
    following_podcasts: list[PydanticObjectId] = []

    class Settings:
        name = "users"

    def __str__(self) -> str:
        return f"User(id={self.id}, user_id={self.user_id}, following_podcasts={self.following_podcasts})"

    def __repr__(self) -> str:
        return self.__str__()
