from datetime import datetime

from beanie import Document, PydanticObjectId


class Podcast(Document):
    ppid: str
    title: str
    feed_url: str

    link: str | None
    latest_episode_date: datetime | None = None

    class Settings:
        name = "podcasts"

    def __str__(self) -> str:
        return f"Podcast(id={self.id}, ppid={self.ppid} title={self.title} feed_url={self.feed_url} link={self.link}, latest_episode_date={self.latest_episode_date})"

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
