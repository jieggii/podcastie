from minicfg import Field, Minicfg, minicfg_prefix
from minicfg.caster import to_int


@minicfg_prefix("BOT")
class Env(Minicfg):
    @minicfg_prefix("TELEGRAM_BOT")
    class TelegramBot(Minicfg):
        TOKEN: str = Field(attach_file_field=True)

    @minicfg_prefix("MONGO")
    class Mongo(Minicfg):
        HOST: str = Field()
        PORT: int = Field(caster=to_int)
        DATABASE: str = Field(attach_file_field=True)
