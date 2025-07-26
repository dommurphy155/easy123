import os
import pytz
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file if present


class Config:
    # Telegram Bot
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Hugging Face Ranker
    HF_API_TOKEN: str = os.getenv("HF_API_KEY", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # CV Data
    CV_TEXT: str = os.getenv("CV_TEXT", "")
    CV_FILEPATH: str = os.getenv("CV_FILEPATH", "assets/cv.pdf")
    CV_TEXTFILEPATH: str = os.getenv("CV_TEXTFILEPATH", "")

    # Geolocation for filtering
    LEIGH_COORDINATES: dict = {"lat": 53.4981, "lon": -2.5197}
    LOCATION_POSTCODE: str = os.getenv("LOCATION_POSTCODE", "WN7 1NX")
    LOCATION_RADIUS_MILES: float = float(os.getenv("LOCATION_RADIUS_MILES", "5.0"))
    TIMEZONE = pytz.timezone("Europe/London")

    # Salary Thresholds
    MIN_SALARY_PER_HOUR: float = float(os.getenv("MIN_SALARY_PER_HOUR", "11.0"))
    MIN_SALARY_PER_YEAR: int = int(os.getenv("MIN_SALARY_PER_YEAR", "17500"))

    # Job Batch Limits
    SCRAPE_LIMIT_PER_RUN: int = int(os.getenv("SCRAPE_LIMIT_PER_RUN", "33"))
    JOBS_PER_TELEGRAM_BATCH: int = int(os.getenv("JOBS_PER_TELEGRAM_BATCH", "8"))
    MAX_JOBS_PER_SCRAPE: int = int(os.getenv("MAX_JOBS_PER_SCRAPE", "25"))
    DAILY_JOB_LIMIT: int = int(os.getenv("DAILY_JOB_LIMIT", "25"))
    MAX_JOBS_PER_BATCH: int = int(os.getenv("MAX_JOBS_PER_BATCH", "8"))
    JOB_BATCH_SIZE: int = int(os.getenv("JOB_BATCH_SIZE", "5"))

    # Timing (scrape/send)
    SCRAPE_TIMES: list[str] = os.getenv("SCRAPE_TIMES", "10:00,15:00,18:10").split(",")
    SEND_TIMES: list[str] = os.getenv("SEND_TIMES", "10:30,17:30,21:00").split(",")
    SCRAPE_DELAY_SECONDS: float = float(os.getenv("SCRAPE_DELAY_SECONDS", "1.0"))

    # Cookies, Debugging, System
    INDEED_COOKIES_PATH: str = os.getenv("INDEED_COOKIES_PATH", "cookies.json")
    SYSTEM_REPORT_INTERVAL_HOURS: int = int(os.getenv("SYSTEM_REPORT_INTERVAL_HOURS", "5"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


config = Config()
