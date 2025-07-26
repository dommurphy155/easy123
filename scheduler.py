import asyncio
from datetime import datetime, timedelta, time
import logging

from bot_runner import BotRunner
from telegram_bot import TelegramBot
from config import TIMEZONE

bot_bot = BotRunner()
telegram_bot = TelegramBot()

# Active background tasks (to avoid GC of asyncio.create_task)
active_tasks = set()

# ────────────────────────────────
# Utility: Wait until a specific local time
# ────────────────────────────────
async def wait_until(target_time: time):
    now = datetime.now(TIMEZONE)
    target_dt = datetime.combine(now.date(), target_time, tzinfo=TIMEZONE)

    if target_dt < now:
        target_dt += timedelta(days=1)

    sleep_seconds = (target_dt - now).total_seconds()
    await asyncio.sleep(sleep_seconds)


# ────────────────────────────────
# Scrape schedule: 10:00, 15:00, 18:10
# ────────────────────────────────
async def scrape_scheduler():
    scrape_times = [time(10, 0), time(15, 0), time(18, 10)]

    while True:
        now = datetime.now(TIMEZONE).time()
        next_time = min((t for t in scrape_times if t > now), default=scrape_times[0])
        await wait_until(next_time)

        logging.info(f"[scheduler] Running scrape task at {next_time}")
        try:
            await bot_bot.run_scrape()
        except Exception as e:
            logging.exception(f"[scheduler] Error in scrape task: {e}")


# ────────────────────────────────
# Send jobs schedule: 10:30, 17:30, 21:00
# ────────────────────────────────
async def send_jobs_scheduler():
    send_times = [time(10, 30), time(17, 30), time(21, 0)]

    while True:
        now = datetime.now(TIMEZONE).time()
        next_time = min((t for t in send_times if t > now), default=send_times[0])
        await wait_until(next_time)

        logging.info(f"[scheduler] Sending jobs to Telegram at {next_time}")
        try:
            await telegram_bot.send_jobs_to_chat()
        except Exception as e:
            logging.exception(f"[scheduler] Error in send_jobs task: {e}")


# ────────────────────────────────
# Main scheduler entry point
# ────────────────────────────────
async def start_schedulers():
    task1 = asyncio.create_task(scrape_scheduler())
    task2 = asyncio.create_task(send_jobs_scheduler())

    active_tasks.update([task1, task2])
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(start_schedulers())
    except (KeyboardInterrupt, SystemExit):
        logging.warning("[scheduler] Shutdown requested, exiting...")
