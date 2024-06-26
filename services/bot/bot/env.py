from betterconf import Config, field
from betterconf.caster import to_int


class Env(Config):
    class Bot(Config):
        _prefix_ = "BOT"
        TOKEN = field(default=None)
        TOKEN_FILE = field(default=None)

    class Mongo(Config):
        _prefix_ = "MONGO"

        HOST = field()
        PORT = field(caster=to_int)
        DATABASE = field(default=None)
        DATABASE_FILE = field(default=None)


env = Env()
