import os
from dotenv import load_dotenv

load_dotenv()  # Load `.env` if present

class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Hugging Face ranking
    HF_API_TOKEN: str = os.getenv("HF_API_KEY", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Indeed scraping & filter
    SCRAPE_LIMIT_PER_RUN: int = int(os.getenv("SCRAPE_LIMIT_PER_RUN", "33"))
    JOBS_PER_TELEGRAM_BATCH: int = int(os.getenv("JOBS_PER_TELEGRAM_BATCH", "8"))
    DAILY_JOB_LIMIT: int = int(os.getenv("DAILY_JOB_LIMIT", "25"))
    LOCATION_POSTCODE: str = os.getenv("LOCATION_POSTCODE", "WN7 1NX")
    LOCATION_RADIUS_MILES: float = float(os.getenv("LOCATION_RADIUS_MILES", "5.0"))
    MIN_SALARY_PER_HOUR: float = float(os.getenv("MIN_SALARY_PER_HOUR", "11.0"))
    MIN_SALARY_PER_YEAR: int = int(os.getenv("MIN_SALARY_PER_YEAR", "17500"))

    CV_FILEPATH: str = os.getenv("CV_FILEPATH", "assets/cv.pdf")
    CV_TEXTFILEPATH: str = os.getenv("CV_TEXTFILEPATH", "")

    INDEED_COOKIES_PATH: str = os.getenv("INDEED_COOKIES_PATH", "cookies.json")

    MAX_JOBS_PER_SCRAPE: int = int(os.getenv("MAX_JOBS_PER_SCRAPE", "25"))
    JOB_BATCH_SIZE: int = int(os.getenv("JOB_BATCH_SIZE", "5"))
    SCRAPE_DELAY_SECONDS: float = float(os.getenv("SCRAPE_DELAY_SECONDS", "1.0"))

    SCRAPE_TIMES: list[str] = os.getenv("SCRAPE_TIMES", "10:00,15:00,18:10").split(",")
    SEND_TIMES: list[str] = os.getenv("SEND_TIMES", "10:30,17:30,21:00").split(",")

    SYSTEM_REPORT_INTERVAL_HOURS: int = int(os.getenv("SYSTEM_REPORT_INTERVAL_HOURS", "5"))

    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

config = Config()
