import httpx
from bs4 import BeautifulSoup
import asyncio
import logging

BASE_URL = "https://uk.indeed.com/jobs"
LOCATION = "Leigh WN7 1NX"  # Use the config location if needed
MAX_JOBS = 33
JOB_TYPE = "part-time"


async def fetch_jobs(session, start=0):
    params = {
        "q": JOB_TYPE,
        "l": LOCATION,
        "start": start,
        "limit": 50,  # Indeed usually paginates by 10 or 50 jobs; adjust if needed
        "jt": JOB_TYPE,
    }
    try:
        resp = await session.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logging.warning(f"[IndeedScraper] HTTP error fetching jobs start={start}: {e}")
        return None


def parse_job_card(card):
    # Job card HTML structures can vary, so parse carefully and defensively
    try:
        job_id = card.get("data-jk")
        title_tag = card.find("h2", {"class": "jobTitle"})
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        company_tag = card.find("span", {"class": "companyName"})
        company = company_tag.get_text(strip=True) if company_tag else "Unknown"
        location_tag = card.find("div", {"class": "companyLocation"})
        location = location_tag.get_text(strip=True) if location_tag else "Unknown"
        salary_tag = card.find("div", {"class": "salary-snippet"})
        salary = salary_tag.get_text(strip=True) if salary_tag else ""
        url = f"https://uk.indeed.com/viewjob?jk={job_id}" if job_id else ""

        if not job_id:
            return None

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "url": url,
        }
    except Exception as e:
        logging.warning(f"[IndeedScraper] Failed parsing job card: {e}")
        return None


async def scrape_indeed_jobs():
    async with httpx.AsyncClient() as session:
        all_jobs = []
        start = 0
        while len(all_jobs) < MAX_JOBS:
            html = await fetch_jobs(session, start=start)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select("div.job_seen_beacon")  # standard container for jobs

            if not job_cards:
                break

            for card in job_cards:
                job = parse_job_card(card)
                if job:
                    all_jobs.append(job)
                    if len(all_jobs) >= MAX_JOBS:
                        break

            start += 10  # Indeed pagination usually in increments of 10 jobs

        return all_jobs[:MAX_JOBS]


# For quick standalone test
if __name__ == "__main__":
    import asyncio
    jobs = asyncio.run(scrape_indeed_jobs())
    print(f"Scraped {len(jobs)} jobs")
    for j in jobs:
        print(j)
