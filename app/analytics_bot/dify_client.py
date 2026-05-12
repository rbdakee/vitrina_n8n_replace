import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("analytics.dify")


class DifyClient:
    def __init__(self, base_url: str, bearer_token: str, timeout: float = 120.0) -> None:
        self._url = f"{base_url.rstrip('/')}/chat-messages"
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=15.0),
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def ask(self, query: str, user: str) -> str | None:
        """Send a streaming chat-message request and return the final thought/answer."""
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "user": user,
        }

        events: list[dict[str, Any]] = []
        async with self._client.stream("POST", self._url, json=payload) as response:
            response.raise_for_status()
            async for raw_line in response.aiter_lines():
                if not raw_line:
                    continue
                line = raw_line.lstrip()
                if not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if not chunk:
                    continue
                try:
                    events.append(json.loads(chunk))
                except json.JSONDecodeError:
                    logger.debug("Skipping non-JSON SSE chunk: %r", chunk)

        if not events:
            return None

        for event in reversed(events):
            if event.get("event") == "agent_thought" and event.get("thought"):
                return event["thought"]

        for event in reversed(events):
            if event.get("event") == "message_end":
                return event.get("answer") or None

        last = events[-1]
        return last.get("thought") or last.get("answer")
