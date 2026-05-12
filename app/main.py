import asyncio
import logging
import signal

from .analytics_bot.bot import run as run_analytics
from .config import settings
from .ivitrina_bot.bot import run as run_ivitrina
from .logging_config import setup_logging


async def _amain() -> None:
    setup_logging(settings.log_dir, settings.log_level)
    log = logging.getLogger("app")
    log.info("Starting bots: ivitrina + analytics")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def _shutdown(signum: int) -> None:
        if not stop.done():
            log.info("Received signal %s, shutting down", signum)
            stop.set_result(None)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown, sig)
        except NotImplementedError:
            # Windows: signal handlers via add_signal_handler aren't supported.
            signal.signal(sig, lambda s, _f: _shutdown(s))

    tasks = [
        asyncio.create_task(run_ivitrina(), name="ivitrina"),
        asyncio.create_task(run_analytics(), name="analytics"),
    ]

    await asyncio.wait(
        [*tasks, stop],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in tasks:
        if not task.done():
            task.cancel()

    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logging.getLogger("app").exception("Bot task %s crashed", task.get_name())

    log.info("Shutdown complete")


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
