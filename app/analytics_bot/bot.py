import logging

from aiogram import Bot, Dispatcher

from ..config import settings
from ..telegram_session import build_session
from .dify_client import DifyClient
from .handlers import build_router

logger = logging.getLogger("analytics")


async def run() -> None:
    bot = Bot(
        token=settings.vitrina_ai_bot_token,
        session=build_session(settings.telegram_proxy),
    )
    dify = DifyClient(
        base_url=settings.dify_api_base,
        bearer_token=settings.dify_bearer_token,
    )

    dp = Dispatcher()
    dp.include_router(build_router(dify))

    logger.info("Starting analytics bot (polling)")
    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await dify.close()
        await bot.session.close()
        logger.info("analytics bot stopped")
