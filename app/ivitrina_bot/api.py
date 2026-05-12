import logging
from typing import Any

import httpx

logger = logging.getLogger("ivitrina.api")


class VitrinaClient:
    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search(
        self,
        params: dict[str, Any],
        limit: int = 5,
        offset: int | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {k: v for k, v in params.items() if v not in (None, "", "null")}
        query["limit"] = limit
        if offset is not None:
            query["offset"] = offset

        url = f"{self._base_url}/api/properties/search"
        logger.info("Search request: %s", query)
        response = await self._client.get(url, params=query)
        response.raise_for_status()
        return response.json()
