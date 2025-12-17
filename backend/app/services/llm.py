"""
LLM service for CV parsing and job analysis using Claude

Now uses Redis caching for distributed caching across servers and persistence
"""
from typing import Optional, Dict, Any
import json
import logging
import hashlib
from anthropic import Anthropic
from app.config import settings
from app.services.redis_cache import (
    cache_get, cache_set,
    build_cv_parse_key, build_job_extract_key,
    TTL_30_DAYS, TTL_7_DAYS
)

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None


def parse_cv_with_llm(cv_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse CV text using Claude Haiku to extract structured information

    Args:
        cv_text: Raw CV text extracted from file

    Returns:
        Dictionary with parsed CV data or None if parsing fails

    The returned dictionary contains:
    - name: Full name
    - email: Email address
    - phone: Phone number
    - summary: Professional summary
    - skills: List of skills
    - experience: List of work experience entries
    - education: List of education entries
    - years_of_experience: Estimated years of experience
    """
    if not client:
        logger.warning("Anthropic API key not configured, skipping LLM parsing")
        return None

    # Generate cache key from CV text hash
    cv_hash = hashlib.sha256(cv_text.encode()).hexdigest()
    cache_key = build_cv_parse_key(cv_hash)

    # Check Redis cache first
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        logger.info(f"Redis cache hit for CV parsing: {cv_hash[:8]}...")
        return cached_result

    logger.info(f"Redis cache miss for CV parsing: {cv_hash[:8]}..., calling LLM")

    prompt = f"""Extract structured information from this CV. Return ONLY valid JSON, no other text.

{{
  "name": "string",
  "email": "string or null",
  "phone": "string or null",
  "summary": "brief professional summary",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{
      "company": "string",
      "title": "string",
      "start_date": "YYYY-MM or null",
      "end_date": "YYYY-MM or null or 'present'",
      "description": "brief description"
    }}
  ],
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field": "string or null",
      "end_date": "YYYY or null"
    }}
  ],
  "years_of_experience": number
}}

CV Text:
---
{cv_text}
---

Return only the JSON object, no markdown formatting or explanations."""

    try:
        # Use Claude Haiku for fast, cost-effective extraction
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            temperature=0,  # Deterministic for extraction
            timeout=30.0,  # 30 second timeout
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])  # Remove first and last lines
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

        # Parse JSON response
        parsed_data = json.loads(response_text)

        logger.info(f"Successfully parsed CV for: {parsed_data.get('name', 'Unknown')}")

        # Cache the result in Redis (30-day TTL)
        cache_set(cache_key, parsed_data, ttl_seconds=TTL_30_DAYS)
        logger.info(f"Cached CV parse result in Redis for 30 days")

        return parsed_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response was: {response_text[:200]}...")
        return None
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        return None


def extract_job_requirements(job_title: str, job_company: str, job_description: str) -> Optional[Dict[str, Any]]:
    """
    Extract structured job requirements using Claude Haiku

    Args:
        job_title: Job title
        job_company: Company name
        job_description: Job description text

    Returns:
        Dictionary with extracted requirements or None if extraction fails

    The returned dictionary contains:
    - required_skills: List of required skills
    - nice_to_have_skills: List of nice-to-have skills
    - experience_years_min: Minimum years of experience
    - experience_years_max: Maximum years of experience
    - education: Education requirement
    - languages: Required languages
    - job_type: Type of job (permanent, contract, etc.)
    - remote_type: Remote work policy (full, hybrid, onsite)
    """
    if not client:
        logger.warning("Anthropic API key not configured, skipping LLM extraction")
        return None

    # Generate cache key from job content hash
    job_content = f"{job_title}|{job_company}|{job_description}"
    job_hash = hashlib.sha256(job_content.encode()).hexdigest()
    # For job extraction, we'll use the hash directly as it's not tied to a specific job ID yet
    cache_key = f"job_extract_hash:{job_hash}"

    # Check Redis cache first
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        logger.info(f"Redis cache hit for job extraction: {job_hash[:8]}...")
        return cached_result

    logger.info(f"Redis cache miss for job extraction: {job_hash[:8]}..., calling LLM")

    prompt = f"""Extract job requirements from this posting. Return ONLY valid JSON, no other text.

{{
  "required_skills": ["skill1", "skill2", ...],
  "nice_to_have_skills": ["skill1", "skill2", ...],
  "experience_years_min": number or null,
  "experience_years_max": number or null,
  "education": "string or null",
  "languages": ["English", ...],
  "job_type": "permanent" | "contract" | "freelance" | "part-time",
  "remote_type": "full" | "hybrid" | "onsite"
}}

Job Posting:
---
Title: {job_title}
Company: {job_company}
Description: {job_description}
---

Return only the JSON object, no markdown formatting or explanations."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            temperature=0,
            timeout=30.0,  # 30 second timeout
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

        parsed_data = json.loads(response_text)

        logger.info(f"Successfully extracted requirements for: {job_title} at {job_company}")

        # Cache the result in Redis (7-day TTL)
        cache_set(cache_key, parsed_data, ttl_seconds=TTL_7_DAYS)
        logger.info(f"Cached job extraction result in Redis for 7 days")

        return parsed_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        return None
