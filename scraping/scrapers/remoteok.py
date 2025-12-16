"""
RemoteOK Scraper

RemoteOK provides a JSON API at https://remoteok.com/api
This is the easiest source to start with.
"""

import httpx
import json
from datetime import datetime
from typing import Optional


REMOTEOK_API_URL = "https://remoteok.com/api"


async def fetch_jobs() -> list[dict]:
    """Fetch jobs from RemoteOK API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            REMOTEOK_API_URL,
            headers={
                "User-Agent": "CareerAgent/0.1.0 (job search assistant)"
            },
            timeout=30.0,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # First item is metadata, skip it
        jobs = data[1:] if len(data) > 1 else []
        
        return [normalize_job(job) for job in jobs]


def normalize_job(raw: dict) -> dict:
    """Normalize RemoteOK job to our schema."""
    
    # Parse salary if present
    salary_min = None
    salary_max = None
    if raw.get("salary_min"):
        try:
            salary_min = int(raw["salary_min"])
        except (ValueError, TypeError):
            pass
    if raw.get("salary_max"):
        try:
            salary_max = int(raw["salary_max"])
        except (ValueError, TypeError):
            pass
    
    # Parse date
    posted_at = None
    if raw.get("date"):
        try:
            posted_at = datetime.fromisoformat(raw["date"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    
    return {
        "source": "remoteok",
        "source_id": str(raw.get("id", "")),
        "url": raw.get("url", ""),
        "title": raw.get("position", ""),
        "company": raw.get("company", ""),
        "description": raw.get("description", ""),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",  # RemoteOK is USD-centric
        "location": raw.get("location", "Remote"),
        "remote_type": "full",  # RemoteOK is all remote
        "job_type": detect_job_type(raw),
        "tags": raw.get("tags", []),
        "posted_at": posted_at,
        "raw_data": raw,
    }


def detect_job_type(raw: dict) -> str:
    """Detect if job is contract, freelance, or permanent."""
    text = f"{raw.get('position', '')} {raw.get('description', '')}".lower()
    
    if any(kw in text for kw in ["contract", "contractor", "freelance", "6 month", "6-month"]):
        return "contract"
    if any(kw in text for kw in ["part-time", "part time"]):
        return "part-time"
    
    return "permanent"


async def scrape_and_save() -> dict:
    """
    Scrape RemoteOK and save jobs to database with logging.
    Automatically triggers matching for new jobs.

    Returns:
        Dictionary with scrape statistics including matching results
    """
    import sys
    sys.path.insert(0, "/Users/denisenanni/Documents/MyWorkspace/career-agent/backend")

    from app.database import get_db_session
    from app.services.scraper import ScraperService

    # Start scrape log
    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="remoteok")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from RemoteOK...")
        jobs = await fetch_jobs()
        print(f"Found {len(jobs)} jobs")

        # Save to database
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="remoteok")

            # Update scrape log with success
            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="completed",
                jobs_found=stats["total"],
                jobs_new=stats["new"],
            )

        print(f"Saved to database: {stats['new']} new, {stats['updated']} updated")

        # Trigger automatic matching for new jobs if any
        if stats["new"] > 0:
            print(f"Triggering automatic matching for {stats['new']} new jobs...")
            try:
                from app.models import Job, User
                from app.services.matching import match_job_with_all_users

                matches_created = 0
                with get_db_session() as db:
                    # Get the newly added jobs (last N jobs from remoteok)
                    new_jobs = (
                        db.query(Job)
                        .filter(Job.source == "remoteok")
                        .order_by(Job.scraped_at.desc())
                        .limit(stats["new"])
                        .all()
                    )

                    # Match each new job with all users
                    for job in new_jobs:
                        job_matches = await match_job_with_all_users(db, job, min_score=60.0)
                        matches_created += len(job_matches)

                stats["matches_created"] = matches_created
                print(f"Created {matches_created} matches")

            except Exception as match_error:
                print(f"Warning: Automatic matching failed: {match_error}")
                stats["matches_created"] = 0
                stats["matching_error"] = str(match_error)
        else:
            stats["matches_created"] = 0

        return stats

    except Exception as e:
        # Update scrape log with error
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="failed",
                error=str(e),
            )
        raise


# CLI for testing
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        # Check if --save flag is provided
        save_to_db = "--save" in sys.argv

        if save_to_db:
            # Scrape and save to database
            stats = await scrape_and_save()
            print(f"\nTotal: {stats['total']}, New: {stats['new']}, Updated: {stats['updated']}")
        else:
            # Just fetch and display
            print("Fetching jobs from RemoteOK...")
            jobs = await fetch_jobs()
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                # Show salary range if present
                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

                if with_salary:
                    print("Salary ranges:")
                    for job in with_salary[:5]:
                        print(f"  {job['title']}: ${job['salary_min']:,} - ${job['salary_max']:,}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
