import secrets
from typing import Any

from .parser import PARAM_KEYS

TELEGRAM_CALLBACK_LIMIT = 64
PREFIX = "seeMore"
PREFIX_TOKEN = "seeMoreT"

_token_store: dict[str, dict[str, Any]] = {}


def _stringify(value: Any) -> str:
    if value is None:
        return "null"
    return str(value)


def build_callback(params: dict[str, Any], offset: int) -> str:
    parts = [PREFIX] + [_stringify(params.get(k)) for k in PARAM_KEYS] + [str(offset)]
    direct = "_".join(parts)
    if len(direct.encode("utf-8")) <= TELEGRAM_CALLBACK_LIMIT:
        return direct

    token = secrets.token_urlsafe(8)
    _token_store[token] = {**{k: params.get(k) for k in PARAM_KEYS}, "offset": offset}
    return f"{PREFIX_TOKEN}_{token}"


def parse_callback(data: str) -> tuple[dict[str, Any], int] | None:
    if data.startswith(f"{PREFIX_TOKEN}_"):
        token = data[len(PREFIX_TOKEN) + 1 :]
        stored = _token_store.get(token)
        if not stored:
            return None
        params = {k: stored.get(k) for k in PARAM_KEYS}
        offset = int(stored.get("offset", 0))
        return params, offset

    if not data.startswith(f"{PREFIX}_"):
        return None

    parts = data.split("_")
    expected = 1 + len(PARAM_KEYS) + 1
    if len(parts) < expected:
        return None

    values = parts[1 : 1 + len(PARAM_KEYS)]
    offset_str = parts[1 + len(PARAM_KEYS)]
    params = {
        key: (None if val == "null" else val)
        for key, val in zip(PARAM_KEYS, values)
    }
    try:
        offset = int(offset_str)
    except ValueError:
        return None
    return params, offset


def advance_offset(data: str, step: int = 5) -> str:
    """Rebuild callback_data for the next page (mirrors n8n behavior)."""
    parsed = parse_callback(data)
    if parsed is None:
        raise ValueError(f"Unparseable callback_data: {data!r}")
    params, offset = parsed
    return build_callback(params, offset + step)
