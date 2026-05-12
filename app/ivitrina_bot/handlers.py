import logging
from typing import Any

import httpx
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from .api import VitrinaClient
from .callback import advance_offset, build_callback, parse_callback
from .formatter import format_results
from .parser import QueryParser

logger = logging.getLogger("ivitrina")

LIMIT = 5
SEARCHING_TEXT = "Идет поиск..."
MORE_BUTTON_TEXT = "Показать еще"


def _more_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=MORE_BUTTON_TEXT, callback_data=callback_data)]]
    )


def build_router(parser: QueryParser, api: VitrinaClient) -> Router:
    router = Router(name="ivitrina")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer(
            "Напишите запрос по недвижимости — например, «Найди 2-комнатные в Астане до 35 млн»."
        )

    @router.message(F.text)
    async def on_text(message: Message, bot: Bot) -> None:
        user_text = message.text or ""
        logger.info("[%s] query: %s", message.from_user.id if message.from_user else "?", user_text)

        placeholder = await message.answer(SEARCHING_TEXT)

        try:
            params = await parser.parse(user_text)
        except Exception:
            logger.exception("OpenAI parse failed")
            await bot.edit_message_text(
                chat_id=placeholder.chat.id,
                message_id=placeholder.message_id,
                text="Не удалось разобрать запрос. Попробуйте переформулировать.",
            )
            return

        try:
            data = await api.search(params, limit=LIMIT)
        except httpx.TimeoutException:
            logger.warning("Vitrina API search timed out for params=%s", params)
            await bot.edit_message_text(
                chat_id=placeholder.chat.id,
                message_id=placeholder.message_id,
                text="Сервер Vitrina не ответил вовремя. Попробуйте ещё раз через минуту.",
            )
            return
        except Exception:
            logger.exception("Vitrina API search failed")
            await bot.edit_message_text(
                chat_id=placeholder.chat.id,
                message_id=placeholder.message_id,
                text="Ошибка при обращении к Vitrina API. Попробуйте позже.",
            )
            return

        items: list[dict[str, Any]] = data.get("items") or []
        total: int = data.get("total", 0)
        text = format_results(items)

        reply_markup = None
        if items and total > LIMIT:
            reply_markup = _more_keyboard(build_callback(params, offset=0))

        await bot.edit_message_text(
            chat_id=placeholder.chat.id,
            message_id=placeholder.message_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    @router.message(~F.text)
    async def on_non_text(message: Message) -> None:
        await message.answer("Напишите запрос по недвижимости текстом.")

    @router.callback_query(F.data.startswith(("seeMore_", "seeMoreT_")))
    async def on_more(query: CallbackQuery, bot: Bot) -> None:
        if query.data is None or query.message is None:
            await query.answer()
            return

        parsed = parse_callback(query.data)
        if parsed is None:
            await query.answer("Сессия устарела, отправьте поиск заново.", show_alert=True)
            return
        params, prev_offset = parsed
        next_offset = prev_offset + LIMIT

        # Strip the inline keyboard from the previous result so it can't be reused.
        try:
            await bot.edit_message_reply_markup(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                reply_markup=None,
            )
        except Exception:
            logger.debug("Could not strip keyboard from previous message", exc_info=True)

        await query.answer()

        try:
            data = await api.search(params, limit=LIMIT, offset=next_offset)
        except httpx.TimeoutException:
            logger.warning("Vitrina API pagination timed out for offset=%s", next_offset)
            await bot.send_message(
                query.message.chat.id,
                "Сервер Vitrina не ответил вовремя. Попробуйте нажать «Показать еще» снова.",
            )
            return
        except Exception:
            logger.exception("Vitrina API pagination failed")
            await bot.send_message(query.message.chat.id, "Ошибка при загрузке следующей страницы.")
            return

        items: list[dict[str, Any]] = data.get("items") or []
        total: int = data.get("total", 0)
        text = format_results(items)

        reply_markup = None
        if total > LIMIT:
            reply_markup = _more_keyboard(advance_offset(query.data, step=LIMIT))

        await bot.send_message(
            chat_id=query.message.chat.id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    return router
