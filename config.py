import os
from dotenv import load_dotenv
from typing import Optional


load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Hugging Face API
    HF_API_TOKEN: str = os.getenv("HF_API_KEY", "")  # Match .env key exactly
    HF_MODEL: str = os.getenv("HF_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Scraping
    SCRAPE_LIMIT_PER_RUN: int = int(os.getenv("SCRAPE_LIMIT_PER_RUN", "33"))
    JOBS_PER_TELEGRAM_BATCH: int = int(os.getenv("JOBS_PER_TELEGRAM_BATCH", "8"))
    DAILY_JOB_LIMIT: int = int(os.getenv("DAILY_JOB_LIMIT", "25"))  # per platform

    # Location filter
    LOCATION_POSTCODE: str = os.getenv("LOCATION_POSTCODE", "WN7 1NX")
    LOCATION_RADIUS_MILES: float = float(os.getenv("LOCATION_RADIUS_MILES", "5.0"))

    # Salary filter
    MIN_SALARY_PER_HOUR: float = float(os.getenv("MIN_SALARY_PER_HOUR", "11.0"))
    MIN_SALARY_PER_YEAR: int = int(os.getenv("MIN_SALARY_PER_YEAR", "17500"))

    # CV and Filtering
    CV_FILEPATH: str = os.getenv("CV_FILEPATH", "assets/cv.pdf")
    CV_TEXTFILEPATH: Optional[str] = os.getenv("CV_TEXTFILEPATH")

    # Indeed cookies path for auto apply
    INDEED_COOKIES_PATH: str = os.getenv("INDEED_COOKIES_PATH", "cookies.json")

    # Maximum number of jobs to scrape per run
    MAX_JOBS_PER_SCRAPE: int = 25

    # Batch size for jobs sent to Telegram
    JOB_BATCH_SIZE: int = int(os.getenv("JOB_BATCH_SIZE", "5"))

    # Delay between scrapes or processing items (seconds)
    SCRAPE_DELAY_SECONDS: float = float(os.getenv("SCRAPE_DELAY_SECONDS", "1.0"))

    # Timing (UK local times in 24h format HH:MM)
    SCRAPE_TIMES: list[str] = os.getenv("SCRAPE_TIMES", "08:30,13:45,17:00").split(",")
    SEND_TIMES: list[str] = os.getenv("SEND_TIMES", "09:00,18:00,21:00").split(",")

    # Monitoring
    SYSTEM_REPORT_INTERVAL_HOURS: int = int(os.getenv("SYSTEM_REPORT_INTERVAL_HOURS", "5"))

    # Debug flag
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


config = Config()

# Hardcoded coordinates for Leigh (WN7 1NX) — center point for job filtering
LEIGH_COORDINATES = {
    "lat": 53.4975,
    "lon": -2.5196,
}
