import asyncio
import logging
import os
import signal
import sys

from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger("easy123")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Import bot modules
try:
    from telegram_bot import TelegramJobBot
    from scheduler import start_scheduler
    from system_monitor import start_system_monitor
except ImportError as e:
    logger.error(f"Missing dependency or import error: {e}")
    sys.exit(1)


async def main():
    logger.info("Starting easy123 job bot")

    # Init Telegram bot (inject job bot instance if needed later)
    telegram_bot = TelegramJobBot(None)

    # Send initial "bot is live" message
    await telegram_bot.send_startup_message()

    # Start background tasks
    scheduler_task = asyncio.create_task(start_scheduler())
    monitor_task = asyncio.create_task(start_system_monitor(telegram_bot))

    # Wait for termination signal
    stop_event = asyncio.Event()

    def shutdown():
        logger.warning("Stop signal received. Shutting down...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    await stop_event.wait()

    # Cancel running tasks
    logger.info("Cancelling all tasks...")
    scheduler_task.cancel()
    monitor_task.cancel()
    await asyncio.gather(scheduler_task, monitor_task, return_exceptions=True)

    logger.info("Bot shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")
        sys.exit(1)
