import asyncio
import logging
import os
import signal







# Load .env variables if present (local dev)
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main():
    logger.info("Starting easy123 job bot")

    # Load config
    # config = Config() # This line is removed as per the edit hint

    # Init Telegram bot instance
    # You must pass a job_bot instance to TelegramJobBot
    # For now, pass None or a real JobBot instance if available
    telegram_bot = TelegramJobBot(None)

    # Confirm connections/startup messages
    await telegram_bot.send_startup_message()

    # Start scheduler and system monitor concurrently
    scheduler_task = asyncio.create_task(start_scheduler())
    monitor_task = asyncio.create_task(start_system_monitor(telegram_bot))

    # Graceful shutdown on signals
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown():
        logger.info("Received stop signal, shutting down...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    await stop_event.wait()

    logger.info("Cancelling tasks")
    scheduler_task.cancel()
    monitor_task.cancel()
    await asyncio.gather(scheduler_task, monitor_task, return_exceptions=True)

    logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
