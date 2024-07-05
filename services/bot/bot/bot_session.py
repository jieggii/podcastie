from typing import Any

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer


class LocalTelegramAPIAiohttpSession(AiohttpSession):
    def __init__(self, base_url: str):
        super().__init__()
        self.api = TelegramAPIServer.from_base(base_url)
