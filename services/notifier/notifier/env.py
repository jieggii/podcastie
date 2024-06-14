from betterconf import Config, field
from betterconf.caster import to_int


class Env(Config):
    class Bot(Config):
        _prefix_ = "BOT"

        TOKEN = field(default=None)
        TOKEN_FILE = field(default=None)

    class Notifier(Config):
        _prefix_ = "NOTIFIER"

        PERIOD = field(caster=to_int)

    class Mongo(Config):
        _prefix_ = "MONGO"

        HOST = field()
        PORT = field(caster=to_int)
        DATABASE = field()
        DATABASE_FILE = field(default=None)


env = Env()
