import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from utils import load_json, chunk_list, async_sleep
from filters import passes_filters
from hf_ranker import HFMatcher
from config import (
    INDEED_SEARCH_URL,
    LEIGH_COORDINATES,
    MAX_JOBS_PER_SCRAPE,
    JOB_BATCH_SIZE,
    SCRAPE_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)

class JobBot:
    def __init__(self, cookies_file, cv_text):
        self.cookies = load_json(cookies_file)
        if not self.cookies:
            raise RuntimeError("Cookies file missing or empty")
        self.cv_text = cv_text
        self.hf_matcher = HFMatcher()
        self.jobs = []

    async def scrape_indeed(self):
        """
        Scrapes jobs from Indeed, returns raw list of jobs with parsed fields
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9",
        }
        cookies_dict = {c['name']: c['value'] for c in self.cookies}

        async with httpx.AsyncClient(cookies=cookies_dict, headers=headers, timeout=30) as client:
            params = {
                "q": "part time",
                "l": f"{LEIGH_COORDINATES[0]},{LEIGH_COORDINATES[1]}",
                "radius": 5,
                "limit": MAX_JOBS_PER_SCRAPE,
                "sort": "date",
            }
            try:
                response = await client.get(INDEED_SEARCH_URL, params=params)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Indeed scraping failed: {e}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.select(".job_seen_beacon")  # Indeed's job cards CSS class

            jobs = []
            for card in job_cards:
                title_tag = card.select_one("h2.jobTitle span")
                company_tag = card.select_one(".companyName")
                location_tag = card.select_one(".companyLocation")
                salary_tag = card.select_one(".salary-snippet")
                job_type = card.select_one(".jobCardReqItem span")

                job = {
                    "title": title_tag.text.strip() if title_tag else "",
                    "company": company_tag.text.strip() if company_tag else "",
                    "location": location_tag.text.strip() if location_tag else "",
                    "salary_text": salary_tag.text.strip() if salary_tag else None,
                    "job_type": job_type.text.strip() if job_type else "",
                    # Placeholder for lat/lon, to parse separately or use geocode API
                    "latitude": LEIGH_COORDINATES[0],
                    "longitude": LEIGH_COORDINATES[1],
                    "url": card.select_one("a.jcs-JobTitle")["href"] if card.select_one("a.jcs-JobTitle") else None,
                }
                jobs.append(job)
                if len(jobs) >= MAX_JOBS_PER_SCRAPE:
                    break
            return jobs

    async def filter_and_score_jobs(self, raw_jobs):
        filtered = []
        for job in raw_jobs:
            # Parse salary into hourly/yearly floats here - simplified example
            salary_hourly = None
            salary_yearly = None
            if job.get("salary_text"):
                salary_text = job["salary_text"].lower()
                if "hour" in salary_text:
                    # Extract number with basic parsing (expand later)
                    try:
                        salary_hourly = float(''.join(filter(lambda c: c.isdigit() or c=='.', salary_text)))
                    except Exception:
                        salary_hourly = None
                elif "year" in salary_text or "annum" in salary_text:
                    try:
                        salary_yearly = float(''.join(filter(lambda c: c.isdigit() or c=='.', salary_text)))
                    except Exception:
                        salary_yearly = None

            cv_score = self.hf_matcher.score(self.cv_text, f"{job['title']} {job['company']} {job['location']}")
            job['cv_score'] = cv_score
            job['salary_hourly'] = salary_hourly
            job['salary_yearly'] = salary_yearly

            # Location filtering
            lat, lon = LEIGH_COORDINATES
            if not passes_filters(job, cv_score, lat, lon):
                continue

            filtered.append(job)
            if len(filtered) >= MAX_JOBS_PER_SCRAPE:
                break
            await async_sleep(SCRAPE_DELAY_SECONDS)  # Rate limit per job

        return filtered

    async def get_job_batches(self):
        raw_jobs = await self.scrape_indeed()
        filtered_jobs = await self.filter_and_score_jobs(raw_jobs)
        return list(chunk_list(filtered_jobs, JOB_BATCH_SIZE))
