from betterconf import Config as BaseConfig
from betterconf import field
from betterconf.caster import to_int
from podcastie_service_config import BotConfig, MongoConfig


class Env(BaseConfig):
    class Bot(BotConfig):
        pass

    class Mongo(MongoConfig):
        pass

    class FeedPoller(BaseConfig):
        _prefix_ = "FEED_POLLER"
        INTERVAL = field(caster=to_int)


env = Env()
