import aiosqlite
import logging
import os
from typing import List, Dict

DB_PATH = os.path.join(os.getcwd(), "jobs.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                url TEXT,
                raw_json TEXT,
                declined INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def save_jobs(jobs: List[Dict]):
    if not jobs:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        for job in jobs:
            try:
                await db.execute("""
                    INSERT OR IGNORE INTO jobs (id, title, company, location, salary, url, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    job["id"],
                    job["title"],
                    job["company"],
                    job["location"],
                    job.get("salary", ""),
                    job["url"],
                    str(job)  # store raw JSON as string fallback
                ))
            except Exception as e:
                logging.warning(f"[db] Failed to save job {job['id']}: {e}")
        await db.commit()


async def load_jobs_from_db() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, title, company, location, salary, url, raw_json
            FROM jobs
            WHERE declined = 0
        """)
        rows = await cursor.fetchall()

    jobs = []
    for row in rows:
        jobs.append({
            "id": row[0],
            "title": row[1],
            "company": row[2],
            "location": row[3],
            "salary": row[4],
            "url": row[5],
            "raw": row[6]
        })
    return jobs


async def get_job_by_id(job_id: str) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, title, company, location, salary, url, raw_json
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        row = await cursor.fetchone()

    if row:
        return {
            "id": row[0],
            "title": row[1],
            "company": row[2],
            "location": row[3],
            "salary": row[4],
            "url": row[5],
            "raw": row[6]
        }
    return None


async def mark_job_as_declined(job_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET declined = 1 WHERE id = ?", (job_id,))
        await db.commit()
