from betterconf import Config

from podcastie_service_config import BotConfig, MongoConfig


class Env(Config):
    class Bot(BotConfig):
        pass

    class Mongo(MongoConfig):
        pass


env = Env()
