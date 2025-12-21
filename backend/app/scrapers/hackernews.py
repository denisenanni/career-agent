"""
HackerNews Who's Hiring Scraper

Uses hnrss.org RSS feed which aggregates job posts from monthly
"Ask HN: Who is hiring?" threads.

Source: https://hnrss.org/whoishiring/jobs
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime
import re
import html


HN_JOBS_RSS_URL = "https://hnrss.org/whoishiring/jobs"


async def fetch_jobs() -> list[dict]:
    """Fetch jobs from HackerNews Who's Hiring RSS feed."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            HN_JOBS_RSS_URL,
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
    """Normalize HN RSS item to our schema."""

    # Get description which contains the actual job posting
    description_raw = get_text(item, "description")
    if not description_raw:
        return None

    description = clean_html(description_raw)

    # Get company from dc:creator (the HN username posting the job)
    creator = item.find("{http://purl.org/dc/elements/1.1/}creator")
    poster_name = creator.text if creator is not None and creator.text else ""

    # Try to extract company and job title from first line of description
    # HN job format usually starts with: "Company Name | Role | Location | ..."
    first_line = description.split("\n")[0] if description else ""
    parts = [p.strip() for p in first_line.split("|")]

    company = parts[0] if parts else poster_name
    title = parts[1] if len(parts) > 1 else "Software Engineer"  # Default title
    location = "Remote"
    remote_type = None

    # Look for location and remote info in parts
    for part in parts[2:] if len(parts) > 2 else []:
        part_lower = part.lower()
        if "remote" in part_lower:
            remote_type = "full"
            if "hybrid" in part_lower:
                remote_type = "hybrid"
            elif "onsite" in part_lower or "on-site" in part_lower:
                remote_type = None
        elif any(loc in part_lower for loc in ["usa", "eu", "uk", "us ", "europe", "worldwide", "sf", "nyc"]):
            location = part

    # If no company found in first line, use poster name
    if not company or company == first_line:
        company = poster_name if poster_name else "Unknown"

    # Parse date
    posted_at = None
    pub_date = get_text(item, "pubDate")
    if pub_date:
        try:
            posted_at = parsedate_to_datetime(pub_date)
        except (ValueError, TypeError):
            pass

    # Get URL (links to HN comment)
    url = get_text(item, "link")

    # Extract source_id from URL (HN item ID)
    source_id = ""
    if url:
        match = re.search(r'id=(\d+)', url)
        if match:
            source_id = match.group(1)

    # Extract salary from title or description
    salary_min, salary_max = extract_salary(f"{first_line} {description}")

    # Detect job type
    job_type = detect_job_type(first_line, description)

    # Extract tech stack as tags
    tags = extract_tech_tags(f"{first_line} {description}")

    return {
        "source": "hackernews",
        "source_id": source_id,
        "url": url,
        "title": title,
        "company": company,
        "description": description[:5000] if description else "",  # Limit description length
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",
        "location": location,
        "remote_type": remote_type or "full",  # Default to full remote if mentioned in HN hiring
        "job_type": job_type,
        "tags": tags,
        "posted_at": posted_at,
        "raw_data": {
            "first_line": first_line,
            "parts": parts,
            "poster": poster_name,
        },
    }


def clean_html(html_text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not html_text:
        return ""

    # Decode HTML entities
    text = html.unescape(html_text)

    # Convert <p> and <br> to newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text).strip()

    return text


def extract_salary(text: str) -> tuple[Optional[int], Optional[int]]:
    """Extract salary range from text."""
    if not text:
        return None, None

    # Common patterns in HN posts
    patterns = [
        r'\$(\d{1,3}),?(\d{3})\s*[-–to]+\s*\$?(\d{1,3}),?(\d{3})',  # $100,000 - $150,000
        r'\$(\d{2,3})k?\s*[-–to]+\s*\$?(\d{2,3})k',  # $100k - $150k
        r'(\d{2,3})k\s*[-–to]+\s*(\d{2,3})k',  # 100k - 150k
        r'\$(\d{2,3})[kK]\+',  # $100k+ (use as minimum)
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if i == 0:  # $100,000 format
                    min_val = int(groups[0] + groups[1])
                    max_val = int(groups[2] + groups[3])
                elif i == 3:  # $100k+ format
                    min_val = int(groups[0]) * 1000
                    max_val = None
                else:  # k format
                    min_val = int(groups[0]) * 1000
                    max_val = int(groups[1]) * 1000
                return min_val, max_val
            except (ValueError, IndexError):
                continue

    return None, None


def detect_job_type(title: str, description: str) -> str:
    """Detect if job is contract, freelance, or permanent."""
    text = f"{title} {description}".lower()

    if any(kw in text for kw in ["contract", "contractor", "freelance", "consulting"]):
        return "contract"
    if any(kw in text for kw in ["part-time", "part time"]):
        return "part-time"
    if any(kw in text for kw in ["intern", "internship"]):
        return "internship"

    return "permanent"


def extract_tech_tags(text: str) -> list[str]:
    """Extract technology tags from job description."""
    # Common tech keywords to look for
    tech_keywords = [
        "python", "javascript", "typescript", "react", "vue", "angular",
        "node", "nodejs", "java", "kotlin", "swift", "go", "golang", "rust",
        "ruby", "rails", "php", "laravel", "django", "flask", "fastapi",
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
        "postgres", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "graphql", "rest", "api", "microservices", "devops", "sre",
        "machine learning", "ml", "ai", "data science", "data engineering",
        "frontend", "backend", "fullstack", "full-stack", "mobile", "ios", "android",
        "c++", "c#", ".net", "scala", "elixir", "haskell", "clojure"
    ]

    text_lower = text.lower()
    found_tags = []

    for tech in tech_keywords:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, text_lower):
            # Normalize tag name
            tag = tech.replace("nodejs", "node.js").replace("golang", "go")
            if tag not in found_tags:
                found_tags.append(tag)

    return found_tags[:15]  # Limit to 15 tags


async def scrape_and_save() -> dict:
    """
    Scrape HackerNews jobs and save to database.

    Returns:
        Dictionary with scrape statistics
    """
    from app.database import get_db_session
    from app.services.scraper import ScraperService

    # Start scrape log
    with get_db_session() as db:
        scraper_service = ScraperService(db)
        scrape_log = scraper_service.create_scrape_log(source="hackernews")
        scrape_log_id = scrape_log.id

    try:
        print("Fetching jobs from HackerNews Who's Hiring...")
        jobs = await fetch_jobs()
        print(f"Found {len(jobs)} jobs")

        # Save to database
        with get_db_session() as db:
            scraper_service = ScraperService(db)
            stats = scraper_service.save_jobs(jobs, source="hackernews")

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
                        .filter(Job.source == "hackernews")
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
if __name__ == "__main__":
    import asyncio
    import json
    import sys

    async def main():
        save_to_db = "--save" in sys.argv

        if save_to_db:
            stats = await scrape_and_save()
            print(f"\nTotal: {stats['total']}, New: {stats['new']}, Updated: {stats['updated']}")
        else:
            print("Fetching jobs from HackerNews Who's Hiring...")
            jobs = await fetch_jobs()
            print(f"Found {len(jobs)} jobs")

            if jobs:
                print("\nSample job:")
                print(json.dumps(jobs[0], indent=2, default=str))

                with_salary = [j for j in jobs if j["salary_min"]]
                print(f"\nJobs with salary info: {len(with_salary)}")

                # Show some tags
                all_tags = set()
                for job in jobs:
                    all_tags.update(job.get("tags", []))
                print(f"Unique tech tags found: {len(all_tags)}")
                print(f"Sample tags: {list(all_tags)[:20]}")

            print("\nTip: Use --save flag to save jobs to database")

    asyncio.run(main())
