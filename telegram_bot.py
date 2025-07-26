import logging
import asyncio
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, MAX_JOBS_PER_BATCH
from filters import filter_and_score_jobs
from utils import load_jobs_from_db, mark_job_as_declined, get_job_by_id


class TelegramJobBot:
    @staticmethod
    def format_job_batch_static(jobs):
        messages = []
        for job in jobs:
            msg = f"*{job['title']}*\n{job['company']} - {job['location']}\n💰 {job.get('salary', 'N/A')}\n[Apply Here]({job['url']})"
            messages.append(msg)
        return messages

    @staticmethod
    def make_inline_keyboard_static(jobs):
        keyboard = []
        for job in jobs:
            keyboard.append([
                InlineKeyboardButton("✅ Accept", callback_data=f"accept:{job['id']}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline:{job['id']}")
            ])
        return [InlineKeyboardMarkup(keyboard[i:i+1]) for i in range(len(keyboard))]


class TelegramBot:
    def __init__(self):
        self.bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

        # Commands
        self.bot_app.add_handler(CommandHandler("test", self.send_random_job))
        self.bot_app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def send_jobs_to_chat(self):
        logging.info("[telegram] Fetching jobs for Telegram dispatch")
        jobs = await load_jobs_from_db()

        if not jobs:
            logging.info("[telegram] No jobs to send")
            return

        filtered_jobs = await filter_and_score_jobs(jobs)
        selected_jobs = filtered_jobs[:MAX_JOBS_PER_BATCH]

        for job in selected_jobs:
            await self.send_job(job)

    async def send_random_job(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.info("[telegram] /test command triggered")
        jobs = await load_jobs_from_db()
        if not jobs:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="No jobs available.")
            return

        filtered_jobs = await filter_and_score_jobs(jobs)
        if not filtered_jobs:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="No suitable jobs found.")
            return

        job = random.choice(filtered_jobs)
        await self.send_job(job)

    async def send_job(self, job):
        message = f"*{job['title']}* at _{job['company']}_\n\n"
        message += f"💷 Salary: {job.get('salary', 'N/A')}\n"
        message += f"📍 Location: {job.get('location', 'N/A')}\n"
        message += f"🔗 [Apply Here]({job['url']})"

        buttons = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{job['id']}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{job['id']}")
            ]
        ]

        await self.bot_app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        action, job_id = query.data.split("_", 1)
        job = await get_job_by_id(job_id)

        if not job:
            await query.edit_message_text("Job no longer available.")
            return

        if action == "accept":
            await query.edit_message_text(f"You accepted: {job['title']} at {job['company']}")
        elif action == "decline":
            await mark_job_as_declined(job_id)
            await query.edit_message_text(f"You declined: {job['title']} at {job['company']}")
        else:
            await query.edit_message_text("Unknown action.")

    def run_polling(self):
        self.bot_app.run_polling()
