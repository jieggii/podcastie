import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, NoReturn, Type

OnRetryFunc = Callable[[int, Exception], None]


# @dataclass
# class RetrySettings:
# attempts: int
# interval: int
# exceptions: tuple[Type[Exception], ...]
# until_success: bool

# async def retry_limited(
#     f: Callable[..., Awaitable[Any]],
#     kwargs: dict[Any, Any],
#     *,
#     on_retry: OnRetryFunc,
#     exceptions: tuple[Type[Exception], ...]
# ) -> Any | NoReturn:
#     attempt = 1
#     prev_exception: Exception | None = None
#
#     while True:
#         if attempt > 1:
#             on_retry(attempt, prev_exception)
#         try:
#             return await f(**kwargs)
#         except Exception as e:
#             if attempt == settings.attempts:
#                 raise e
#             if not isinstance(e, settings.exceptions):
#                 raise e
#
#             attempt += 1
#             prev_exception = e
#
#         await asyncio.sleep(settings.interval)
#


async def retry_forever(
    f: Callable[..., Awaitable[Any]],
    kwargs: dict[Any, Any],
    *,
    on_retry: OnRetryFunc,
    exceptions: tuple[Type[Exception], ...],
    interval: int = 0,
) -> Any | NoReturn:
    attempt = 1
    prev_exception: Exception | None = None

    while True:
        if attempt > 1:
            on_retry(attempt, prev_exception)
        try:
            return await f(**kwargs)
        except Exception as e:
            if not isinstance(e, exceptions):
                raise e
            attempt += 1
            prev_exception = e

        await asyncio.sleep(interval)
