from aiogram import Router
from .cta import router as _cta_router
from .handler import router as _handler_router


router = Router()
router.include_routers(_cta_router, _handler_router)