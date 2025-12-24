"""
Authentic Jobs Scraper

Authentic Jobs provides an RSS feed at https://authenticjobs.com/?feed=job_feed
Categories: Design, Development, Marketing, Operations, Creative
"""

import feedparser
import re
import html
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime


AUTHENTICJOBS_RSS_URL = "https://authenticjobs.com/?feed=job_feed"


async def fetch_jobs() -> list[dict]:
    """Fetch jobs from Authentic Jobs RSS feed."""
    # feedparser is synchronous, but we keep async signature for consistency
    feed = feedparser.parse(AUTHENTICJOBS_RSS_URL)

    if feed.bozo:
        # Feed parsing had issues
        raise Exception(f"Failed to parse RSS feed: {feed.bozo_exception}")

    jobs = []
    for entry in feed.entries:
        job = normalize_job(entry)
        if job:
            jobs.append(job)

    return jobs


def normalize_job(entry: dict) -> Optional[dict]:
    """Normalize Authentic Jobs RSS entry to our schema."""

    title = entry.get("title", "").strip()
    if not title:
        return None

    # Get company from job_listing_company namespace field
    company = entry.get("job_listing_company", "")

    # Get location from job_listing_location namespace field
    location = entry.get("job_listing_location", "")

    # Get job type from job_listing_job_type namespace field
    job_type_raw = entry.get("job_listing_job_type", "").lower()

    # Get URL
    url = entry.get("link", "")

    # Extract source_id from URL (e.g., /job/35335/ -> 35335)
    source_id = ""
    if url:
        match = re.search(r"/job/(\d+)", url)
        if match:
            source_id = match.group(1)
        else:
            # Fallback to guid
            source_id = entry.get("id", url)

    # Get description - prefer content:encoded, fallback to summary
    description = ""
    if "content" in entry and entry.content:
        description = entry.content[0].get("value", "")
    elif "summary" in entry:
        description = entry.get("summary", "")

    # Clean HTML from description
    description = clean_html(description)

    # Parse date
    posted_at = None
    if "published_parsed" in entry and entry.published_parsed:
        try:
            posted_at = datetime(*entry.published_parsed[:6])
        except (ValueError, TypeError):
            pass
    elif "published" in entry:
        try:
            posted_at = parsedate_to_datetime(entry.published)
        except (ValueError, TypeError):
            pass

    # Extract salary from description if present
    salary_min, salary_max = extract_salary(description)

    # Determine job type
    job_type = "permanent"
    if "freelance" in job_type_raw:
        job_type = "contract"
    elif "part-time" in job_type_raw or "part time" in job_type_raw:
        job_type = "part-time"
    elif "contract" in job_type_raw:
        job_type = "contract"
    elif "internship" in job_type_raw:
        job_type = "contract"

    # Determine remote type from location
    remote_type = detect_remote_type(location)

    # Extract tags from title and description
    tags = extract_tags(title, description)

    return {
        "source": "authenticjobs",
        "source_id": source_id,
        "url": url,
        "title": title,
        "company": company,
        "description": description[:5000] if description else "",
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD" if salary_min else None,
        "location": location or "Not specified",
        "remote_type": remote_type,
        "job_type": job_type,
        "tags": tags[:15],
        "posted_at": posted_at,
        "raw_data": {
            "job_type_raw": job_type_raw,
            "dc_creator": entry.get("author", ""),
        },
    }


def clean_html(html_text: str) -> str:
    """Remove HTML tags and clean up text."""
    if not html_text:
        return ""

    # Unescape HTML entities
    text = html.unescape(html_text)

    # Replace common HTML elements with appropriate spacing
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.IGNORECASE)

    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\n\s*\n", "\n\n", text)

    return text


def extract_salary(description: str) -> tuple[Optional[int], Optional[int]]:
    """Extract salary range from description text."""
    if not description:
        return None, None

    # Common patterns:
    # "$90,000 – $125,000"
    # "$100k - $150k"
    # "$80,000-$120,000"

    # Pattern for dollar amounts
    patterns = [
        # $90,000 – $125,000 or $90,000 - $125,000
        r"\$(\d{1,3}(?:,\d{3})*)\s*[-–—]\s*\$(\d{1,3}(?:,\d{3})*)",
        # $100k - $150k
        r"\$(\d+)k\s*[-–—]\s*\$(\d+)k",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                min_val = match.group(1).replace(",", "")
                max_val = match.group(2).replace(",", "")

                # Handle "k" notation
                if "k" in pattern.lower():
                    salary_min = int(min_val) * 1000
                    salary_max = int(max_val) * 1000
                else:
                    salary_min = int(min_val)
                    salary_max = int(max_val)

                return salary_min, salary_max
            except (ValueError, IndexError):
                pass

    return None, None


def detect_remote_type(location: str) -> str:
    """Detect remote type from location string."""
    location_lower = location.lower()

    if "remote" in location_lower:
        if "hybrid" in location_lower:
            return "hybrid"
        return "full"
    elif "hybrid" in location_lower:
        return "hybrid"
    else:
        return "onsite"


def extract_tags(title: str, description: str) -> list[str]:
    """Extract relevant tags from title and description."""
    text = f"{title} {description}".lower()

    # Common design/creative tags
    tag_keywords = [
        "ui", "ux", "ui/ux", "product design", "graphic design", "web design",
        "figma", "sketch", "adobe", "photoshop", "illustrator",
        "react", "vue", "angular", "javascript", "typescript", "python",
        "frontend", "front-end", "backend", "back-end", "full-stack", "fullstack",
        "wordpress", "shopify", "webflow",
        "marketing", "seo", "content", "copywriting",
        "motion", "animation", "video", "3d",
        "mobile", "ios", "android", "flutter", "react native",
        "aws", "gcp", "azure", "devops",
    ]

    found_tags = []
    for tag in tag_keywords:
        if tag in text:
            # Normalize tag
            normalized = tag.replace("-", " ").replace("/", " ").title()
            if normalized not in found_tags:
                found_tags.append(normalized)

    return found_tags


async def scrape_and_save() -> dict:
    """Scrape Authentic Jobs and save jobs to database."""
    from app.database import get_db_session
    from app.services.scraper import ScraperService

    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="authenticjobs")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from Authentic Jobs RSS...")
        jobs = await fetch_jobs()
        print(f"Found {len(jobs)} jobs")

        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="authenticjobs")

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
                        .filter(Job.source == "authenticjobs")
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
            print("Fetching jobs from Authentic Jobs RSS...")
            jobs = await fetch_jobs()
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

                if with_salary:
                    print("Salary ranges:")
                    for job in with_salary[:5]:
                        print(f"  {job['title']}: ${job['salary_min']:,} - ${job['salary_max']:,}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
