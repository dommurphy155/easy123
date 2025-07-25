import asyncio
import psutil
import logging
from datetime import datetime, timezone, timedelta
from telegram_bot import TelegramJobBot




logger = logging.getLogger(__name__)

CPU_THRESHOLD = 85.0  # Percent CPU usage to trigger alert
MEM_THRESHOLD = 90.0  # Percent RAM usage to trigger alert
REPORT_INTERVAL_HOURS = 5

async def check_system_health(bot: TelegramJobBot):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    logger.debug(f"CPU Usage: {cpu}%, Memory Usage: {mem}%")

    alerts = []
    if cpu > CPU_THRESHOLD:
        alerts.append(f"🔥 High CPU usage detected: {cpu}%")
    if mem > MEM_THRESHOLD:
        alerts.append(f"🔥 High Memory usage detected: {mem}%")

    if alerts:
        alert_msg = "\n".join(alerts)
        await bot.send_system_alert(alert_msg)
        logger.warning(f"Sent system alert: {alert_msg}")

async def send_system_report(bot: TelegramJobBot):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report = (
        f"🖥️ System Health Report at {now}\n"
        f"CPU Usage: {cpu}%\n"
        f"Memory Usage: {mem}%"
    )
    await bot.send_system_report(report)
    logger.info("Sent system health report")

async def system_monitor_loop(bot: TelegramJobBot):
    hours_since_report = 0
    while True:
        try:
            await check_system_health(bot)
            hours_since_report += 1
            if hours_since_report >= REPORT_INTERVAL_HOURS:
                await send_system_report(bot)
                hours_since_report = 0
            await asyncio.sleep(3600)  # check every hour
        except Exception as e:
            logger.error(f"Error in system monitor loop: {e}")
            await asyncio.sleep(60)  # backoff on error

# Optional function to start monitor in main.py
async def start_system_monitor(bot: TelegramJobBot):
    await system_monitor_loop(bot)
