"""
We Work Remotely Scraper

We Work Remotely provides RSS feeds at https://weworkremotely.com/remote-jobs.rss
One of the largest remote job boards.
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime
import re
import html


WWR_RSS_URL = "https://weworkremotely.com/remote-jobs.rss"


async def fetch_jobs() -> list[dict]:
    """Fetch jobs from We Work Remotely RSS feed."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WWR_RSS_URL,
            headers={
                "User-Agent": "CareerAgent/0.1.0 (job search assistant)"
            },
            timeout=30.0,
        )
        response.raise_for_status()

        # Parse RSS XML
        root = ET.fromstring(response.text)
        jobs = []

        for item in root.findall(".//item"):
            job = normalize_job(item)
            if job:
                jobs.append(job)

        return jobs


def get_text(element, tag: str) -> str:
    """Safely get text from XML element."""
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def normalize_job(item) -> Optional[dict]:
    """Normalize We Work Remotely RSS item to our schema."""

    title_raw = get_text(item, "title")
    if not title_raw:
        return None

    # Title format is usually "Company: Job Title"
    company = ""
    title = title_raw
    if ": " in title_raw:
        parts = title_raw.split(": ", 1)
        company = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else title_raw

    # Get description and clean HTML
    description_raw = get_text(item, "description")
    description = clean_html(description_raw)

    # Parse date
    posted_at = None
    pub_date = get_text(item, "pubDate")
    if pub_date:
        try:
            posted_at = parsedate_to_datetime(pub_date)
        except (ValueError, TypeError):
            pass

    # Get URL
    url = get_text(item, "link")

    # Extract source_id from URL
    source_id = url.split("/")[-1] if url else ""

    # Get category/region tags
    tags = []
    for category in item.findall("category"):
        if category.text:
            tags.append(category.text.strip())

    # Get region element if present
    region = get_text(item, "{http://www.weworkremotely.com}region")
    if region and region not in tags:
        tags.append(region)

    # Extract salary from description if present
    salary_min, salary_max = extract_salary(description)

    return {
        "source": "weworkremotely",
        "source_id": source_id,
        "url": url,
        "title": title,
        "company": company,
        "description": description,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",
        "location": region or "Remote",
        "remote_type": "full",  # WWR is all remote
        "job_type": detect_job_type(title, description),
        "tags": tags,
        "posted_at": posted_at,
        "raw_data": {
            "title_raw": title_raw,
            "description_raw": description_raw[:500] if description_raw else "",
        },
    }


def clean_html(html_text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not html_text:
        return ""

    # Decode HTML entities
    text = html.unescape(html_text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def extract_salary(text: str) -> tuple[Optional[int], Optional[int]]:
    """Extract salary range from text."""
    if not text:
        return None, None

    # Common patterns: $100k-$150k, $100,000 - $150,000, 100k-150k
    patterns = [
        r'\$(\d{1,3}),?(\d{3})\s*[-–to]+\s*\$?(\d{1,3}),?(\d{3})',  # $100,000 - $150,000
        r'\$(\d{2,3})k?\s*[-–to]+\s*\$?(\d{2,3})k',  # $100k - $150k
        r'(\d{2,3})k\s*[-–to]+\s*(\d{2,3})k',  # 100k - 150k
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 4:
                    # $100,000 format
                    min_val = int(groups[0] + groups[1])
                    max_val = int(groups[2] + groups[3])
                else:
                    # k format
                    min_val = int(groups[0]) * 1000
                    max_val = int(groups[1]) * 1000
                return min_val, max_val
            except (ValueError, IndexError):
                continue

    return None, None


def detect_job_type(title: str, description: str) -> str:
    """Detect if job is contract, freelance, or permanent."""
    text = f"{title} {description}".lower()

    if any(kw in text for kw in ["contract", "contractor", "freelance"]):
        return "contract"
    if any(kw in text for kw in ["part-time", "part time"]):
        return "part-time"

    return "permanent"


async def scrape_and_save() -> dict:
    """
    Scrape We Work Remotely and save jobs to database.

    Returns:
        Dictionary with scrape statistics
    """
    from app.database import get_db_session
    from app.services.scraper import ScraperService

    # Start scrape log
    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="weworkremotely")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from We Work Remotely...")
        jobs = await fetch_jobs()
        print(f"Found {len(jobs)} jobs")

        # Save to database
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="weworkremotely")

            # Update scrape log with success
            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="completed",
                jobs_found=stats["total"],
                jobs_new=stats["new"],
            )

        print(f"Saved to database: {stats['new']} new, {stats['updated']} updated")

        # Trigger automatic matching for new jobs
        if stats["new"] > 0:
            print(f"Triggering automatic matching for {stats['new']} new jobs...")
            try:
                from app.models import Job
                from app.services.matching import match_job_with_all_users

                matches_created = 0
                with get_db_session() as db:
                    new_jobs = (
                        db.query(Job)
                        .filter(Job.source == "weworkremotely")
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
            print("Fetching jobs from We Work Remotely...")
            jobs = await fetch_jobs()
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
