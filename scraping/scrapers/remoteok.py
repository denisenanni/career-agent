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


# CLI for testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
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
    
    asyncio.run(main())
