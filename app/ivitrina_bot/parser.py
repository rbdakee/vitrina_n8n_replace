import json
import logging
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger("ivitrina.parser")

SYSTEM_PROMPT = """Ты — помощник по поиску недвижимости.
Пользователь пишет свободно, например:
- "Найди квартиры в Астане до 40 миллионов"
- "Хочу 3-комнатную от 80 кв.м"
- "Покажи ЖК Grand до 30 млн"

Твоя задача — определить параметры для вызова Search Vitrina API.
Если параметр не указан — не включай его. Когда пишут "улица Байтерекова", тебе нужно писать только название улицы  или название ЖК, не нужно дописывать такие слова как Район, Город, Улица, ЖК в ответе

Верни результат строго в JSON-формате:
{
  "price_min": <число или null>,
  "price_max": <число или null>,
  "complex": "<название ЖК или null>",
  "area_min": <число или null>,
  "area_max": <число или null>,
  "rooms_count_min": <число или null>,
  "rooms_count_max": <число или null>,
  "score_min": <число или null>,
  "address": "<строка или null>"
}
"""

PARAM_KEYS = (
    "price_min",
    "price_max",
    "complex",
    "area_min",
    "area_max",
    "rooms_count_min",
    "rooms_count_max",
    "score_min",
    "address",
)


class QueryParser:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def parse(self, user_text: str) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("OpenAI returned non-JSON content: %r", content)
            data = {}
        return {key: data.get(key) for key in PARAM_KEYS}
