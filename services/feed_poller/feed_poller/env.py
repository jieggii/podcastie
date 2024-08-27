from minicfg import Field, Minicfg, minicfg_prefix
from minicfg.caster import to_int


@minicfg_prefix("FEED_POLLER")
class Env(Minicfg):
    class FeedPoller(Minicfg):
        INTERVAL = Field(caster=to_int)

    @minicfg_prefix("TELEGRAM_BOT")
    class TelegramBot(Minicfg):
        TOKEN: str = Field(attach_file_field=True)
        API_HOST: str = Field()
        API_PORT: int = Field(caster=to_int)

    @minicfg_prefix("MONGO")
    class Mongo(Minicfg):
        HOST: str = Field()
        PORT: int = Field(caster=to_int)
        DATABASE: str = Field(attach_file_field=True)
