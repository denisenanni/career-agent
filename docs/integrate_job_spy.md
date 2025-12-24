# Task: Integrate JobSpy for Multi-Board Job Scraping

## Goal

Add JobSpy library to scrape jobs from LinkedIn, Indeed, Glassdoor, Google Jobs, and ZipRecruiter alongside existing scrapers (RemoteOK, Authentic Jobs).

---

## Overview

JobSpy is a Python library that scrapes multiple job boards with a single API call.

**Repository:** https://github.com/speedyapply/JobSpy

**Supported boards:**
- Indeed (most reliable, no rate limiting)
- Google Jobs
- Glassdoor
- ZipRecruiter
- LinkedIn (aggressive rate limiting - needs proxies)

---

## Implementation

### 1. Install Package

Add to `backend/requirements.txt`:
```
python-jobspy>=1.1.79
```

### 2. Create JobSpy Scraper

Create `backend/app/scrapers/jobspy_scraper.py`:

```python
from jobspy import scrape_jobs
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def scrape_jobspy(
    search_term: str = "software engineer",
    location: str = "Remote",
    sites: list[str] = ["indeed", "google"],
    results_per_site: int = 50,
    hours_old: int = 72,
    is_remote: bool = True,
    country_indeed: str = "USA",
) -> list[dict]:
    """
    Scrape multiple job boards using JobSpy.
    
    Args:
        search_term: Job search query
        location: Location filter
        sites: List of sites to scrape (indeed, google, glassdoor, linkedin, zip_recruiter)
        results_per_site: Number of results per site
        hours_old: Only jobs posted within this many hours
        is_remote: Filter for remote jobs only
        country_indeed: Country for Indeed/Glassdoor searches
    
    Returns:
        List of jobs in standard format
    """
    try:
        jobs_df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location,
            results_wanted=results_per_site,
            hours_old=hours_old,
            is_remote=is_remote,
            country_indeed=country_indeed,
        )
        
        logger.info(f"JobSpy found {len(jobs_df)} jobs from {sites}")
        
        # Convert DataFrame to standard job format
        jobs = []
        for _, row in jobs_df.iterrows():
            job = normalize_jobspy_job(row)
            if job:
                jobs.append(job)
        
        return jobs
        
    except Exception as e:
        logger.error(f"JobSpy scraping failed: {e}")
        return []


def normalize_jobspy_job(row) -> Optional[dict]:
    """Convert JobSpy DataFrame row to standard job format."""
    try:
        # Build location string
        city = row.get("city") or ""
        state = row.get("state") or ""
        country = row.get("country") or ""
        location_parts = [p for p in [city, state, country] if p]
        location = ", ".join(location_parts) if location_parts else "Remote"
        
        # Determine remote type
        is_remote = row.get("is_remote", False)
        remote_type = "full" if is_remote else None
        
        # Generate unique source_id from URL
        job_url = row.get("job_url", "")
        source_id = str(hash(job_url)) if job_url else None
        
        if not source_id or not row.get("title"):
            return None
        
        return {
            "source": f"jobspy_{row.get('site', 'unknown')}",
            "source_id": source_id,
            "title": row.get("title"),
            "company": row.get("company"),
            "description": row.get("description") or "",
            "url": job_url,
            "location": location,
            "salary_min": row.get("min_amount"),
            "salary_max": row.get("max_amount"),
            "salary_currency": row.get("currency") or "USD",
            "remote_type": remote_type,
            "posted_at": row.get("date_posted") or datetime.utcnow(),
            "tags": [],  # JobSpy doesn't provide tags, LLM extraction handles this
            "job_type": row.get("job_type"),  # fulltime, parttime, contract, internship
        }
    except Exception as e:
        logger.warning(f"Failed to normalize job: {e}")
        return None
```

### 3. Integrate with Scraper Service

Update `backend/app/services/scraper.py`:

```python
from app.scrapers import remoteok, authentic_jobs, jobspy_scraper

async def scrape_all_sources():
    """Run all job scrapers."""
    all_jobs = []
    
    # Existing scrapers
    try:
        remoteok_jobs = await remoteok.scrape()
        all_jobs.extend(remoteok_jobs)
        logger.info(f"RemoteOK: {len(remoteok_jobs)} jobs")
    except Exception as e:
        logger.error(f"RemoteOK failed: {e}")
    
    try:
        authentic_jobs_list = await authentic_jobs.scrape()
        all_jobs.extend(authentic_jobs_list)
        logger.info(f"Authentic Jobs: {len(authentic_jobs_list)} jobs")
    except Exception as e:
        logger.error(f"Authentic Jobs failed: {e}")
    
    # JobSpy - multiple boards at once
    try:
        jobspy_jobs = await jobspy_scraper.scrape_jobspy(
            search_term="developer OR engineer OR designer",
            is_remote=True,
            sites=["indeed", "google"],  # Start without LinkedIn
            results_per_site=100,
            hours_old=72,
        )
        all_jobs.extend(jobspy_jobs)
        logger.info(f"JobSpy: {len(jobspy_jobs)} jobs")
    except Exception as e:
        logger.error(f"JobSpy failed: {e}")
    
    # Dedupe and save to database
    saved_count = await save_jobs_to_db(all_jobs)
    logger.info(f"Total saved: {saved_count} jobs")
    
    return saved_count
```

### 4. Add Multiple Search Terms (Optional Enhancement)

For better coverage, run multiple searches:

```python
async def scrape_jobspy_comprehensive() -> list[dict]:
    """Run multiple JobSpy searches for different job types."""
    all_jobs = []
    
    searches = [
        {"search_term": "software engineer", "is_remote": True},
        {"search_term": "frontend developer", "is_remote": True},
        {"search_term": "backend developer", "is_remote": True},
        {"search_term": "fullstack developer", "is_remote": True},
        {"search_term": "3D artist", "is_remote": True},
        {"search_term": "UI UX designer", "is_remote": True},
    ]
    
    for search in searches:
        jobs = await scrape_jobspy(
            search_term=search["search_term"],
            is_remote=search["is_remote"],
            sites=["indeed", "google"],
            results_per_site=50,
        )
        all_jobs.extend(jobs)
    
    return all_jobs
```

---

## Configuration

Add to `backend/app/config.py` (optional):

```python
class Settings(BaseSettings):
    # ... existing settings
    
    # JobSpy settings
    jobspy_enabled: bool = True
    jobspy_sites: list[str] = ["indeed", "google"]
    jobspy_results_per_site: int = 100
    jobspy_hours_old: int = 72
    jobspy_proxies: list[str] = []  # For LinkedIn: ["user:pass@host:port"]
```

---

## Files to Create/Modify

**Create:**
- `backend/app/scrapers/jobspy_scraper.py`

**Modify:**
- `backend/requirements.txt` - Add python-jobspy
- `backend/app/services/scraper.py` - Integrate JobSpy
- `backend/app/config.py` - Add JobSpy settings (optional)

---

## Important Notes

### Rate Limiting

| Site | Rate Limit | Recommendation |
|------|-----------|----------------|
| Indeed | None | Safe to use freely |
| Google | Light | Safe to use |
| Glassdoor | Moderate | Use with caution |
| ZipRecruiter | Moderate | Use with caution |
| LinkedIn | Aggressive | Skip or use proxies |

**Start with Indeed + Google only.** Add others later if needed.

### Proxies (for LinkedIn)

If you want LinkedIn, add proxy support:

```python
jobs_df = scrape_jobs(
    site_name=["linkedin"],
    search_term="...",
    proxies=["user:pass@host:port", "host2:port2"],
)
```

### Job Limits

All boards cap at ~1000 jobs per search. For more coverage:
- Use multiple search terms
- Run searches for different locations
- Schedule regular scraping (daily)

---

## Testing

1. Install package: `pip install python-jobspy`
2. Test standalone:
   ```python
   from jobspy import scrape_jobs
   jobs = scrape_jobs(
       site_name=["indeed"],
       search_term="software engineer",
       location="Remote",
       results_wanted=10,
       is_remote=True,
   )
   print(f"Found {len(jobs)} jobs")
   print(jobs.head())
   ```
3. Run full scraper and verify jobs appear in database
4. Check deduplication works (no duplicate jobs from same source)

---

## Acceptance Criteria

- [ ] python-jobspy installed and working
- [ ] JobSpy scraper returns normalized job format
- [ ] Jobs saved to database with correct source (jobspy_indeed, jobspy_google, etc.)
- [ ] Deduplication works across all sources
- [ ] Scraper handles errors gracefully (doesn't crash if one site fails)
- [ ] Jobs appear in /api/jobs endpoint
- [ ] Jobs match with user CVs correctly