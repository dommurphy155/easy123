import httpx
from bs4 import BeautifulSoup
import asyncio
import logging

BASE_URL = "https://uk.indeed.com/jobs"
LOCATION = "Leigh WN7 1NX"
JOB_TYPE = "part-time"


async def fetch_jobs(session, start=0, limit=50):
    params = {
        "q": JOB_TYPE,
        "l": LOCATION,
        "start": start,
        "limit": limit,
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
    try:
        job_id = card.get("data-jk")
        if not job_id:
            return None

        title_tag = card.find("h2", {"class": "jobTitle"})
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        company_tag = card.find("span", {"class": "companyName"})
        company = company_tag.get_text(strip=True) if company_tag else "Unknown"

        location_tag = card.find("div", {"class": "companyLocation"})
        location = location_tag.get_text(strip=True) if location_tag else "Unknown"

        salary_tag = card.find("div", {"class": "salary-snippet"})
        salary = salary_tag.get_text(strip=True) if salary_tag else ""

        url = f"https://uk.indeed.com/viewjob?jk={job_id}"

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


async def scrape_indeed_jobs(limit=33, filters=None):
    async with httpx.AsyncClient() as session:
        all_jobs = []
        start = 0

        while len(all_jobs) < limit:
            html = await fetch_jobs(session, start=start)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select("div.job_seen_beacon")

            if not job_cards:
                break

            for card in job_cards:
                job = parse_job_card(card)
                if job:
                    all_jobs.append(job)
                    if len(all_jobs) >= limit:
                        break

            start += 10

        return all_jobs[:limit]


# Manual test runner
if __name__ == "__main__":
    import asyncio

    results = asyncio.run(scrape_indeed_jobs(limit=10))
    print(f"Scraped {len(results)} jobs")
    for job in results:
        print(job)
