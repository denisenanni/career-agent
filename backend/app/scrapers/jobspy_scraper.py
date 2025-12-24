"""
JobSpy Multi-Board Scraper

Uses the python-jobspy library to scrape multiple job boards:
- Indeed (most reliable, no rate limiting)
- Google Jobs (light rate limiting)
- Glassdoor (moderate rate limiting)
- ZipRecruiter (moderate rate limiting)
- LinkedIn (aggressive rate limiting - requires proxies)

We start with Indeed + Google only for safety.
"""

import logging
from datetime import datetime
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Default search terms for comprehensive job coverage
DEFAULT_SEARCH_TERMS = [
    "software engineer",
    "frontend developer",
    "backend developer",
    "fullstack developer",
    "UI UX designer",
    "3D artist",
]

# Safe sites to scrape (no aggressive rate limiting)
DEFAULT_SITES = ["indeed", "google"]


def fetch_jobs(
    search_term: str = "software engineer",
    location: str = "Remote",
    sites: list[str] = None,
    results_per_site: int = 50,
    hours_old: int = 72,
    is_remote: bool = True,
    country_indeed: str = "USA",
) -> pd.DataFrame:
    """
    Fetch jobs from multiple boards using JobSpy.

    Args:
        search_term: Job search query
        location: Location filter
        sites: List of sites to scrape (indeed, google, glassdoor, linkedin, zip_recruiter)
        results_per_site: Number of results per site
        hours_old: Only jobs posted within this many hours
        is_remote: Filter for remote jobs only
        country_indeed: Country for Indeed/Glassdoor searches

    Returns:
        DataFrame of job listings
    """
    from jobspy import scrape_jobs

    if sites is None:
        sites = DEFAULT_SITES

    jobs_df = scrape_jobs(
        site_name=sites,
        search_term=search_term,
        location=location,
        results_wanted=results_per_site,
        hours_old=hours_old,
        is_remote=is_remote,
        country_indeed=country_indeed,
    )

    logger.info(f"JobSpy found {len(jobs_df)} jobs for '{search_term}' from {sites}")
    return jobs_df


def normalize_job(row: pd.Series) -> Optional[dict]:
    """
    Convert JobSpy DataFrame row to standard job format.

    Args:
        row: pandas Series from JobSpy DataFrame

    Returns:
        Normalized job dict or None if invalid
    """
    try:
        title = row.get("title", "")
        if not title:
            return None

        job_url = row.get("job_url", "")
        if not job_url:
            return None

        # Generate unique source_id from URL hash
        source_id = str(abs(hash(job_url)))

        # Build location string
        city = row.get("city") or ""
        state = row.get("state") or ""
        country = row.get("country") or ""
        location_parts = [p for p in [city, state, country] if p]
        location = ", ".join(location_parts) if location_parts else "Remote"

        # Determine remote type
        is_remote = row.get("is_remote", False)
        if is_remote:
            remote_type = "full"
        elif "hybrid" in location.lower():
            remote_type = "hybrid"
        else:
            remote_type = "onsite"

        # Get site name for source
        site = row.get("site", "unknown")
        source = f"jobspy_{site}"

        # Handle salary
        salary_min = row.get("min_amount")
        salary_max = row.get("max_amount")
        salary_currency = row.get("currency") or "USD"

        # Convert salary to int if present
        if pd.notna(salary_min):
            salary_min = int(salary_min)
        else:
            salary_min = None

        if pd.notna(salary_max):
            salary_max = int(salary_max)
        else:
            salary_max = None

        # Handle date
        date_posted = row.get("date_posted")
        if pd.notna(date_posted):
            if isinstance(date_posted, str):
                try:
                    posted_at = datetime.fromisoformat(date_posted.replace("Z", "+00:00"))
                except ValueError:
                    posted_at = datetime.utcnow()
            elif isinstance(date_posted, datetime):
                posted_at = date_posted
            else:
                posted_at = datetime.utcnow()
        else:
            posted_at = datetime.utcnow()

        # Normalize job type
        job_type_raw = str(row.get("job_type", "")).lower()
        if "part" in job_type_raw:
            job_type = "part-time"
        elif "contract" in job_type_raw or "temp" in job_type_raw:
            job_type = "contract"
        elif "intern" in job_type_raw:
            job_type = "contract"
        else:
            job_type = "permanent"

        # Get description
        description = row.get("description") or ""
        if len(description) > 5000:
            description = description[:5000]

        # Extract tags from title and description
        tags = extract_tags(title, description)

        return {
            "source": source,
            "source_id": source_id,
            "url": job_url,
            "title": title,
            "company": row.get("company") or "Unknown",
            "description": description,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency if salary_min else None,
            "location": location,
            "remote_type": remote_type,
            "job_type": job_type,
            "tags": tags[:15],
            "posted_at": posted_at,
            "raw_data": {
                "site": site,
                "job_type_raw": job_type_raw,
                "company_url": row.get("company_url"),
            },
        }
    except Exception as e:
        logger.warning(f"Failed to normalize job: {e}")
        return None


def extract_tags(title: str, description: str) -> list[str]:
    """Extract relevant tags from title and description."""
    text = f"{title} {description}".lower()

    tag_keywords = [
        "react", "vue", "angular", "javascript", "typescript", "python",
        "java", "go", "rust", "c++", "c#", ".net",
        "frontend", "front-end", "backend", "back-end", "full-stack", "fullstack",
        "aws", "gcp", "azure", "devops", "kubernetes", "docker",
        "mobile", "ios", "android", "flutter", "react native",
        "ui", "ux", "ui/ux", "figma", "sketch",
        "3d", "blender", "unity", "unreal", "maya",
        "machine learning", "ml", "ai", "data science",
        "node", "django", "fastapi", "spring",
    ]

    found_tags = []
    for tag in tag_keywords:
        if tag in text:
            normalized = tag.replace("-", " ").replace("/", " ").title()
            if normalized not in found_tags:
                found_tags.append(normalized)

    return found_tags


async def fetch_all_jobs(
    search_terms: list[str] = None,
    sites: list[str] = None,
    results_per_site: int = 50,
    hours_old: int = 72,
) -> list[dict]:
    """
    Fetch jobs for multiple search terms.

    Args:
        search_terms: List of search terms to use
        sites: List of sites to scrape
        results_per_site: Results per site per search
        hours_old: Only jobs within this many hours

    Returns:
        List of normalized job dicts
    """
    if search_terms is None:
        search_terms = DEFAULT_SEARCH_TERMS
    if sites is None:
        sites = DEFAULT_SITES

    all_jobs = []
    seen_urls = set()

    for search_term in search_terms:
        try:
            jobs_df = fetch_jobs(
                search_term=search_term,
                sites=sites,
                results_per_site=results_per_site,
                hours_old=hours_old,
                is_remote=True,
            )

            for _, row in jobs_df.iterrows():
                job = normalize_job(row)
                if job and job["url"] not in seen_urls:
                    all_jobs.append(job)
                    seen_urls.add(job["url"])

        except Exception as e:
            logger.error(f"Failed to fetch jobs for '{search_term}': {e}")
            continue

    logger.info(f"Total unique jobs fetched: {len(all_jobs)}")
    return all_jobs


async def scrape_and_save() -> dict:
    """Scrape JobSpy boards and save jobs to database."""
    from app.database import get_db_session
    from app.services.scraper import ScraperService

    # Create scrape log
    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="jobspy")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from JobSpy (Indeed + Google)...")
        jobs = await fetch_all_jobs()
        print(f"Found {len(jobs)} unique jobs")

        # Save jobs to database
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="jobspy")

            scraper_service.update_scrape_log(
                scrape_log_id=scrape_log_id,
                status="completed",
                jobs_found=stats["total"],
                jobs_new=stats["new"],
            )

        print(f"Saved to database: {stats['new']} new, {stats['updated']} updated")

        # Trigger matching for new jobs
        if stats["new"] > 0:
            print(f"Triggering automatic matching for {stats['new']} new jobs...")
            try:
                from app.models import Job
                from app.services.matching import match_job_with_all_users

                matches_created = 0
                with get_db_session() as db:
                    # Get new jobs (from any jobspy source)
                    new_jobs = (
                        db.query(Job)
                        .filter(Job.source.startswith("jobspy_"))
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
            print("Fetching jobs from JobSpy...")
            jobs = await fetch_all_jobs(
                search_terms=["software engineer"],
                results_per_site=10,
            )
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
