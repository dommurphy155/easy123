import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import config
from utils import send_system_report


    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logger = logging.getLogger(__name__)

class TelegramJobBot:
    def __init__(self, job_bot):
        self.job_bot = job_bot
        self.app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("sendjobs", self.send_jobs))
        self.app.add_handler(CommandHandler("report", self.report))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome to Easy123 JobBot! Use /sendjobs to get the latest jobs.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "/start - Start bot\n"
            "/help - This help message\n"
            "/status - Show system/job status\n"
            "/sendjobs - Send next batch of jobs\n"
            "/report - Get system health report\n"
        )
        await update.message.reply_text(help_text)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Example placeholder, expand with real stats
        status_msg = "System Status:\nJobs queued: {}\nCPU usage: --%\nMemory usage: --%".format(len(self.job_bot.jobs))
        await update.message.reply_text(status_msg)

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Calls system report utility, sends result
        report = await send_system_report()
        await update.message.reply_text(report)

    async def send_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        batches = await self.job_bot.get_job_batches()
        if not batches:
            await update.message.reply_text("No jobs found right now. Try again later.")
            return

        for batch in batches:
            text = self.format_job_batch(batch)
            keyboard = self.make_inline_keyboard(batch)
            await update.message.reply_text(text, reply_markup=keyboard)
            # Minimal pause to avoid Telegram flood limits
            await asyncio.sleep(1)

    def format_job_batch(self, jobs):
        # Format job details + emoji etc
        lines = []
        for i, job in enumerate(jobs, 1):
            lines.append(f"🧰 *{job['title']}* @ {job['company']}\n"
                         f"📍 {job['location']}\n"
                         f"💷 Salary: {job.get('salary_text', 'N/A')}\n"
                         f"🔗 [Job Link](https://www.indeed.com{job['url']})\n"
                         f"🔎 Relevance Score: {job.get('cv_score', 0):.2f}\n")
        return "\n\n".join(lines)

    def make_inline_keyboard(self, jobs):
        buttons = []
        for job in jobs:
            buttons.append([
                InlineKeyboardButton(f"✅ Accept {job['title'][:20]}", callback_data=f"accept|{job['url']}"),
                InlineKeyboardButton(f"❌ Decline {job['title'][:20]}", callback_data=f"decline|{job['url']}"),
            ])
        return InlineKeyboardMarkup(buttons)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data.split("|")
        if len(data) != 2:
            await query.edit_message_text("Invalid action.")
            return
        action, job_url = data
        if action == "accept":
            # Stub auto-apply logic
            success = await self.auto_apply(job_url)
            if success:
                # mark_job_as_accepted(job_url) # This line was removed as per edit hint
                await query.edit_message_text("🎉 Successfully applied! Good luck!")
            else:
                await query.edit_message_text(f"⚠️ Auto-apply failed. Here’s the link to apply manually:\n{job_url}")
        elif action == "decline":
            # mark_job_as_declined(job_url) # This line was removed as per edit hint
            await query.edit_message_text("🗑️ Job declined and removed.")

    async def auto_apply(self, job_url):
        # TODO: Implement actual auto-apply with cookies + HTTP post
        # Return True if success, False if fail
        await asyncio.sleep(0.5)  # Simulate work
        return False  # Placeholder

    def run(self):
        self.app.run_polling()
