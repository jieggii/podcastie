from structlog import get_logger

from aiohttp import ClientConnectorError

class Shit:
    errno = 1
    strerror = "123"

l = get_logger()
l.warning("war!", e=ClientConnectorError("hello", Shit()))