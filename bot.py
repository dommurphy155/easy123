import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from utils import load_json, chunk_list, async_sleep
from filters import passes_filters
from hf_ranker import HFMatcher
from config import config, LEIGH_COORDINATES


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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9",
        }
        cookies_dict = {c['name']: c['value'] for c in self.cookies}
        search_url = "https://uk.indeed.com/jobs"
        params = {
            "q": "part time",
            "l": "Leigh",
            "radius": config.LOCATION_RADIUS_MILES,
            "sort": "date",
            "limit": config.MAX_JOBS_PER_SCRAPE,
        }

        try:
            async with httpx.AsyncClient(cookies=cookies_dict, headers=headers, timeout=30) as client:
                resp = await client.get(search_url, params=params)
                resp.raise_for_status()
        except Exception as e:
            logger.error(f"Indeed scraping failed: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.select(".job_seen_beacon")
        jobs = []
        for card in job_cards:
            title = card.select_one("h2.jobTitle span")
            company = card.select_one(".companyName")
            location = card.select_one(".companyLocation")
            salary = card.select_one(".salary-snippet")
            job_type = card.select_one(".jobCardReqItem span")
            link_tag = card.select_one("a.jcs-JobTitle")

            job = {
                "title": title.text.strip() if title else "",
                "company": company.text.strip() if company else "",
                "location": location.text.strip() if location else "",
                "salary_text": salary.text.strip() if salary else None,
                "job_type": job_type.text.strip() if job_type else "",
                "latitude": LEIGH_COORDINATES["lat"],
                "longitude": LEIGH_COORDINATES["lon"],
                "url": f"https://uk.indeed.com{link_tag.get('href')}" if link_tag and link_tag.get("href") else None,
            }
            jobs.append(job)
            if len(jobs) >= config.MAX_JOBS_PER_SCRAPE:
                break
        return jobs

    async def filter_and_score_jobs(self, raw_jobs):
        filtered = []
        for job in raw_jobs:
            salary_hourly = None
            salary_yearly = None
            if job.get("salary_text"):
                s = job["salary_text"].lower()
                try:
                    val = float(''.join(filter(lambda c: c.isdigit() or c == '.', s)))
                    if "hour" in s:
                        salary_hourly = val
                    elif "year" in s or "annum" in s:
                        salary_yearly = val
                except Exception:
                    pass

            cv_score = self.hf_matcher.score(self.cv_text, f"{job['title']} {job['company']} {job['location']}")
            job.update({
                "cv_score": cv_score,
                "salary_hourly": salary_hourly,
                "salary_yearly": salary_yearly,
            })

            if not passes_filters(job, cv_score, LEIGH_COORDINATES["lat"], LEIGH_COORDINATES["lon"]):
                continue

            filtered.append(job)
            if len(filtered) >= config.MAX_JOBS_PER_SCRAPE:
                break
            await async_sleep(getattr(config, "SCRAPE_DELAY_SECONDS", 1))

        return filtered

    async def get_job_batches(self):
        raw = await self.scrape_indeed()
        filtered = await self.filter_and_score_jobs(raw)
        batch_size = getattr(config, "JOB_BATCH_SIZE", 5)
        return list(chunk_list(filtered, batch_size))
