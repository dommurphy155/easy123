import asyncio
import logging
from datetime import time
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from hf_ranker import HFMatcher
from scraper.indeed_scraper import scrape_indeed_jobs
from config import config, LEIGH_COORDINATES
from filters import passes_filters
from telegram_bot import TelegramJobBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hf = HFMatcher()

async def do_scrape_and_send(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running scheduled scrape")
    jobs = await scrape_indeed_jobs(limit=33, filters={
        "lat": LEIGH_COORDINATES["lat"],
        "lon": LEIGH_COORDINATES["lon"],
        "part_time": True,
    })
    # score & filter
    filtered = []
    for job in jobs:
        cv_score = hf.score(config.CV_TEXT or "", f"{job['title']} {job['company']} {job['location']}")
        job['cv_score'] = cv_score
        if passes_filters(job, cv_score, LEIGH_COORDINATES["lat"], LEIGH_COORDINATES["lon"]):
            filtered.append(job)
        if len(filtered) >= config.JOB_BATCH_SIZE:
            break
    if not filtered:
        context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text="No jobs found.")
        return
    for batch in [filtered[i:i+config.JOB_BATCH_SIZE] for i in range(0, len(filtered), config.JOB_BATCH_SIZE)]:
        text = TelegramJobBot.format_job_batch_static(batch)
        keyboard = TelegramJobBot.make_inline_keyboard_static(batch)
        await context.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=text, reply_markup=keyboard, parse_mode="Markdown")
        await asyncio.sleep(1)

async def test_command(update, context):
    # `/test` command: send a random job immediately
    jobs = await scrape_indeed_jobs(limit=1, filters={"lat": LEIGH_COORDINATES["lat"], "lon": LEIGH_COORDINATES["lon"], "part_time": True})
    if not jobs:
        await update.message.reply_text("No jobs available for test.")
        return
    job = jobs[0]
    job['cv_score'] = hf.score(config.CV_TEXT or "", f"{job['title']} {job['company']} {job['location']}")
    if not passes_filters(job, job['cv_score'], LEIGH_COORDINATES["lat"], LEIGH_COORDINATES["lon"]):
        await update.message.reply_text("Test job didn’t pass filters.")
        return
    text = TelegramJobBot.format_job_batch_static([job])
    keyboard = TelegramJobBot.make_inline_keyboard_static([job])
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def start_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    jb = app.job_queue

    telegram_bot = TelegramJobBot(job_bot=None)  # Only using static helpers here
    # Register commands
    app.add_handler(CommandHandler("start", telegram_bot.start))
    app.add_handler(CommandHandler("help", telegram_bot.help))
    app.add_handler(CommandHandler("status", telegram_bot.status))
    app.add_handler(CommandHandler("sendjobs", telegram_bot.send_jobs))
    app.add_handler(CommandHandler("report", telegram_bot.report))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CallbackQueryHandler(telegram_bot.button_handler))

    # Schedule jobs
    for sched_time in ("10:00", "15:00", "18:10"):
        hh, mm = map(int, sched_time.split(":"))
        jb.run_daily(do_scrape_and_send, time(hh, mm), days=(0,1,2,3,4,5,6), name=f"scrape_{sched_time}")
    # send tasks 10:30,17:30,21:00
    for send_time in ("10:30", "17:30", "21:00"):
        hh, mm = map(int, send_time.split(":"))
        jb.run_daily(lambda ctx: asyncio.create_task(do_scrape_and_send(ctx)), time(hh, mm), days=(0,1,2,3,4,5,6), name=f"send_{send_time}")

    logger.info("Bot starting polling")
    await app.run_polling()

def main():
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.error("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")
        return
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
