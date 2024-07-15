import asyncio
from typing import Any, Awaitable, Callable, NoReturn
import aiohttp

RetryCallback = Callable[[int, Exception], None]
ExceptionCheckerFunc = Callable[[Exception], bool]


def _is_retryable_exception(e: Exception) -> bool:
    """returns true if need to retry"""
    if isinstance(e, aiohttp.ClientConnectorError):
        e: aiohttp.ClientConnectorError
        if e.os_error.errno == -3:
            return True
    return False


class HTTPRetryer:
    def __init__(self, interval: int, max_attempts: int):
        self.interval = interval
        self.max_attempts = max_attempts

    async def wrap(
            self,
            f: Callable[..., Awaitable[Any]],
            kwargs: dict[Any, Any],
            retry_callback: RetryCallback | None = None,
    ) -> Any | NoReturn:
        attempt = 1
        prev_exception: Exception | None = None

        while True:
            if attempt > 1:
                if retry_callback:
                    retry_callback(attempt, prev_exception)
            try:
                return await f(**kwargs)
            except Exception as e:
                if not _is_retryable_exception(e):
                    raise e
                if attempt == self.max_attempts:
                    raise e

                attempt += 1
                prev_exception = e

            await asyncio.sleep(self.interval)
