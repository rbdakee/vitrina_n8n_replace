import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from .dify_client import DifyClient

logger = logging.getLogger("analytics")

TYPING_TEXT = "печатаю ..."


def build_router(dify: DifyClient) -> Router:
    router = Router(name="analytics")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer("Задайте вопрос по данным.")

    @router.message(F.text)
    async def on_text(message: Message, bot: Bot) -> None:
        user_text = message.text or ""
        chat_id = message.chat.id
        username = message.from_user.username if message.from_user else ""
        user_field = f"{username} {chat_id}".strip()

        logger.info("[%s] query: %s", chat_id, user_text)
        await bot.send_message(chat_id, TYPING_TEXT)

        try:
            answer = await dify.ask(user_text, user=user_field)
        except Exception:
            logger.exception("Dify request failed")
            await bot.send_message(chat_id, "Ошибка при обращении к аналитике. Попробуйте позже.")
            return

        if not answer:
            await bot.send_message(chat_id, "Пустой ответ от модели.")
            return

        await bot.send_message(chat_id, answer)

    @router.message(~F.text)
    async def on_non_text(message: Message) -> None:
        await message.answer("Отправьте вопрос текстом.")

    return router
