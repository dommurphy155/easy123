from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import asyncio
import logging

logger = logging.getLogger(__name__)
UK_TZ = ZoneInfo("Europe/London")

# Scheduled times
SCRAPE_TIMES = [time(8, 30), time(13, 45), time(17, 0)]
SEND_TIMES = [time(9, 0), time(18, 0), time(21, 0)]

async def wait_until(target_time: time):
    now = datetime.now(UK_TZ)
    target_dt = now.replace(hour=target_time.hour, minute=target_time.minute,
                           second=0, microsecond=0)
    if target_dt <= now:
        target_dt += timedelta(days=1)
    wait_seconds = (target_dt - now).total_seconds()
    logger.info(f"Sleeping for {wait_seconds} seconds until {target_time}")
    await asyncio.sleep(wait_seconds)

async def schedule_task(task_func, schedule_times):
    while True:
        now = datetime.now(UK_TZ).time()
        # Find next scheduled time
        future_times = [t for t in schedule_times if t > now]
        next_time = future_times[0] if future_times else schedule_times[0]

        await wait_until(next_time)

        try:
            await task_func()
        except Exception as e:
            logger.error(f"Error running scheduled task {task_func.__name__}: {e}")

async def scrape_task():
    logger.info("Starting scrape task")
    # This should trigger scraping via bot.py
    # Assuming bot.py is accessible or singleton, here stub:
    # Ideally inject bot.py instance or call through an interface
    # For now, just log placeholder
    logger.info("Scraping jobs (implement call)")
    # TODO: call bot.py.run_scrape()
    logger.info("Scrape task completed")

async def send_jobs_task():
    logger.info("Starting send jobs task")
    # This should trigger sending jobs via telegram_bot.py
    # Assuming TelegramJobBot instance accessible or singleton, here stub:
    # Ideally inject TelegramJobBot instance or call through an interface
    # For now, just log placeholder
    logger.info("Sending job alerts to Telegram (implement call)")
    # TODO: call TelegramJobBot.send_jobs()
    logger.info("Send jobs task completed")

async def start_scheduler():
    # Run scrape and send_jobs loops concurrently
    await asyncio.gather(
        schedule_task(scrape_task, SCRAPE_TIMES),
        schedule_task(send_jobs_task, SEND_TIMES)
    )
