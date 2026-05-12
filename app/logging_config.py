import logging
import logging.handlers
import os
from pathlib import Path


_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _file_handler(log_dir: Path, filename: str, level: int) -> logging.Handler:
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_dir / filename,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def setup_logging(log_dir: str, level: str = "INFO") -> tuple[logging.Logger, logging.Logger]:
    root_level = getattr(logging, level.upper(), logging.INFO)
    log_path = Path(log_dir)

    stream = logging.StreamHandler()
    stream.setLevel(root_level)
    stream.setFormatter(logging.Formatter(_FORMAT))

    root = logging.getLogger()
    root.setLevel(root_level)
    root.handlers.clear()
    root.addHandler(stream)

    # Suppress polling noise (getUpdates spam every few seconds).
    for noisy in (
        "aiogram.event",
        "aiogram.dispatcher",
        "aiogram.webhook",
        "aiohttp.access",
        "aiohttp.client",
        "httpx",
        "httpcore",
        "openai",
        "openai._base_client",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    ivitrina = logging.getLogger("ivitrina")
    ivitrina.setLevel(root_level)
    ivitrina.propagate = False
    ivitrina.addHandler(_file_handler(log_path, "ivitrina.log", root_level))
    ivitrina.addHandler(stream)

    analytics = logging.getLogger("analytics")
    analytics.setLevel(root_level)
    analytics.propagate = False
    analytics.addHandler(_file_handler(log_path, "analytics.log", root_level))
    analytics.addHandler(stream)

    return ivitrina, analytics
