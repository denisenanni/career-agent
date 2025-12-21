"""
Jobicy Scraper

Jobicy provides a free JSON API at https://jobicy.com/api/v2/remote-jobs
Well-structured API with good data quality.
"""

import httpx
from datetime import datetime
from typing import Optional
import re


JOBICY_API_URL = "https://jobicy.com/api/v2/remote-jobs"


async def fetch_jobs(count: int = 50) -> list[dict]:
    """Fetch jobs from Jobicy API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            JOBICY_API_URL,
            params={"count": count},
            headers={
                "User-Agent": "CareerAgent/0.1.0 (job search assistant)"
            },
            timeout=30.0,
        )
        response.raise_for_status()

        data = response.json()
        jobs_data = data.get("jobs", [])

        return [normalize_job(job) for job in jobs_data if job]


def normalize_job(raw: dict) -> Optional[dict]:
    """Normalize Jobicy job to our schema."""

    title = raw.get("jobTitle", "")
    if not title:
        return None

    company = raw.get("companyName", "")

    # Get description
    description = raw.get("jobDescription", "")
    # Clean HTML if present
    description = clean_html(description)

    # Parse date
    posted_at = None
    pub_date = raw.get("pubDate")
    if pub_date:
        try:
            # Jobicy format: "2025-12-15 10:30:00"
            posted_at = datetime.fromisoformat(pub_date.replace(" ", "T"))
        except (ValueError, TypeError):
            pass

    # Get URL
    url = raw.get("url", "")

    # Extract source_id from URL or use ID
    source_id = str(raw.get("id", "")) or url.split("/")[-1]

    # Get tags from jobIndustry and jobType
    tags = []
    if raw.get("jobIndustry"):
        tags.extend([t.strip().lower() for t in raw["jobIndustry"] if t])
    if raw.get("jobType"):
        tags.extend([t.strip().lower() for t in raw["jobType"] if t])

    # Extract salary - Jobicy provides annualSalaryMin/Max
    salary_min = None
    salary_max = None
    if raw.get("annualSalaryMin"):
        try:
            salary_min = int(raw["annualSalaryMin"])
        except (ValueError, TypeError):
            pass
    if raw.get("annualSalaryMax"):
        try:
            salary_max = int(raw["annualSalaryMax"])
        except (ValueError, TypeError):
            pass

    # Get location
    location = raw.get("jobGeo", "Remote") or "Remote"

    # Determine remote type
    remote_type = "full"  # Jobicy is all remote jobs

    # Detect job type from jobType field
    job_type = "permanent"
    job_type_raw = raw.get("jobType", [])
    if job_type_raw:
        job_type_str = " ".join(job_type_raw).lower()
        if "contract" in job_type_str:
            job_type = "contract"
        elif "part-time" in job_type_str or "part time" in job_type_str:
            job_type = "part-time"
        elif "freelance" in job_type_str:
            job_type = "contract"

    return {
        "source": "jobicy",
        "source_id": source_id,
        "url": url,
        "title": title,
        "company": company,
        "description": description[:5000] if description else "",
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",
        "location": location,
        "remote_type": remote_type,
        "job_type": job_type,
        "tags": tags[:15],  # Limit tags
        "posted_at": posted_at,
        "raw_data": {
            "jobIndustry": raw.get("jobIndustry"),
            "jobType": raw.get("jobType"),
            "companyLogo": raw.get("companyLogo"),
        },
    }


def clean_html(html_text: str) -> str:
    """Remove HTML tags."""
    if not html_text:
        return ""

    import html
    text = html.unescape(html_text)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


async def scrape_and_save() -> dict:
    """Scrape Jobicy and save jobs to database."""
    from app.database import get_db_session
    from app.services.scraper import ScraperService

    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="jobicy")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from Jobicy...")
        jobs = await fetch_jobs(count=50)
        print(f"Found {len(jobs)} jobs")

        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="jobicy")

            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="completed",
                jobs_found=stats["total"],
                jobs_new=stats["new"],
            )

        print(f"Saved to database: {stats['new']} new, {stats['updated']} updated")

        if stats["new"] > 0:
            print(f"Triggering automatic matching for {stats['new']} new jobs...")
            try:
                from app.models import Job
                from app.services.matching import match_job_with_all_users

                matches_created = 0
                with get_db_session() as db:
                    new_jobs = (
                        db.query(Job)
                        .filter(Job.source == "jobicy")
                        .order_by(Job.scraped_at.desc())
                        .limit(stats["new"])
                        .all()
                    )

                    for job in new_jobs:
                        job_matches = await match_job_with_all_users(db, job, min_score=60.0)
                        matches_created += len(job_matches)

                stats["matches_created"] = matches_created
                print(f"Created {matches_created} matches")

            except Exception as match_error:
                print(f"Warning: Automatic matching failed: {match_error}")
                stats["matches_created"] = 0
        else:
            stats["matches_created"] = 0

        return stats

    except Exception as e:
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="failed",
                error=str(e),
            )
        raise


if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import json
    import sys

    async def main():
        save_to_db = "--save" in sys.argv

        if save_to_db:
            stats = await scrape_and_save()
            print(f"\nTotal: {stats['total']}, New: {stats['new']}, Updated: {stats['updated']}")
        else:
            print("Fetching jobs from Jobicy...")
            jobs = await fetch_jobs()
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
