import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from ..config import settings
from .api import VitrinaClient
from .handlers import build_router
from .parser import QueryParser

logger = logging.getLogger("ivitrina")


async def run() -> None:
    bot = Bot(
        token=settings.sd_ivitrina_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    parser = QueryParser(api_key=settings.openai_api_key, model=settings.openai_model)
    api = VitrinaClient(base_url=settings.vitrina_api_base)

    dp = Dispatcher()
    dp.include_router(build_router(parser, api))

    logger.info("Starting ivitrina bot (polling)")
    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await api.close()
        await bot.session.close()
        logger.info("ivitrina bot stopped")
