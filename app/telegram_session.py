from __future__ import annotations

from urllib.parse import urlparse

from aiogram.client.session.aiohttp import AiohttpSession


def build_session(proxy_url: str | None) -> AiohttpSession:
    """Build an aiogram session, optionally routed through a proxy.

    Supports http(s):// proxies natively via aiohttp, and socks5:// via
    aiohttp_socks.ProxyConnector. Returns a plain AiohttpSession when no
    proxy is configured.
    """
    if not proxy_url:
        return AiohttpSession()

    scheme = urlparse(proxy_url).scheme.lower()

    if scheme in ("http", "https"):
        return AiohttpSession(proxy=proxy_url)

    if scheme in ("socks5", "socks5h", "socks4"):
        from aiohttp_socks import ProxyConnector

        session = AiohttpSession()
        session._connector_type = ProxyConnector  # type: ignore[attr-defined]
        session._connector_init = {"proxy_url": proxy_url}  # type: ignore[attr-defined]
        return session

    raise ValueError(f"Unsupported TELEGRAM_PROXY scheme: {scheme!r}")
