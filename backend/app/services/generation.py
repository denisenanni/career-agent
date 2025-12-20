"""
Application materials generation service using Claude

Generates personalized cover letters and CV highlights with Redis caching
to minimize API costs and provide instant responses for cached content.
"""
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime, timezone
from anthropic import Anthropic
from app.config import settings
from app.services.redis_cache import (
    cache_get, cache_set,
    build_cover_letter_key, build_cv_highlights_key,
    TTL_30_DAYS
)
from app.models.user import User
from app.models.job import Job
from app.models.match import Match

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None


def generate_cover_letter(
    user: User,
    job: Job,
    match: Match
) -> Optional[Dict[str, Any]]:
    """
    Generate a personalized cover letter for a job application

    Args:
        user: User object with profile information
        job: Job object with job details
        match: Match object with matching analysis

    Returns:
        Dictionary with:
        - cover_letter: Generated cover letter text
        - cached: Whether result was from cache
        - generated_at: Timestamp of generation
    """
    if not client:
        logger.warning("Anthropic API key not configured, cannot generate cover letter")
        return None

    # Build cache key
    cache_key = build_cover_letter_key(user.id, job.id)

    # Check Redis cache first
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        logger.info(f"Redis cache hit for cover letter: user={user.id}, job={job.id}")
        return {
            "cover_letter": cached_result["cover_letter"],
            "cached": True,
            "generated_at": cached_result["generated_at"]
        }

    logger.info(f"Redis cache miss for cover letter: user={user.id}, job={job.id}, calling Claude Sonnet")

    # Prepare profile data
    parsed_cv = user.preferences.get("parsed_cv", {}) if user.preferences else {}
    name = parsed_cv.get("name", user.full_name or "")
    skills = ", ".join(user.skills or [])
    years_exp = parsed_cv.get("years_of_experience", user.experience_years or 0)
    summary = parsed_cv.get("summary", "")

    # Format experience entries
    experience_entries = parsed_cv.get("experience", [])
    experience_text = ""
    for i, exp in enumerate(experience_entries[:3], 1):  # Top 3 experiences
        experience_text += f"\n{i}. {exp.get('title', 'Position')} at {exp.get('company', 'Company')}"
        if exp.get('start_date') or exp.get('end_date'):
            experience_text += f" ({exp.get('start_date', '')} - {exp.get('end_date', 'present')})"
        if exp.get('description'):
            experience_text += f"\n   {exp.get('description')}"

    # Prepare job data
    # Note: match.reasoning contains structured analysis, match.analysis is just text
    reasoning = match.reasoning or {}
    required_skills = reasoning.get("job_requirements", {}).get("required_skills", [])
    job_description_excerpt = job.description[:500] if job.description else ""

    # Prepare match analysis
    skill_matches = reasoning.get("matching_skills", [])
    skill_gaps = reasoning.get("missing_skills", [])
    match_score = match.score or 0

    # Build the prompt
    prompt = f"""Write a professional cover letter for this job application. Be genuine and personable while remaining professional.

CANDIDATE INFORMATION:
Name: {name}
Current Skills: {skills}
Years of Experience: {years_exp}
Professional Summary: {summary}

Relevant Experience:{experience_text}

JOB DETAILS:
Position: {job.title}
Company: {job.company}
Required Skills: {', '.join(required_skills[:10])}
Job Description (excerpt): {job_description_excerpt}

MATCH ANALYSIS:
Matching Skills ({len(skill_matches)}): {', '.join(skill_matches[:10])}
Skill Gaps ({len(skill_gaps)}): {', '.join(skill_gaps[:5])}
Match Score: {match_score:.0f}%

INSTRUCTIONS:
1. Keep it under 400 words
2. Address why the candidate is a strong fit (emphasize matching skills)
3. Briefly acknowledge skill gaps and show willingness to learn if relevant
4. Express genuine interest in the company and role
5. Professional but not overly formal tone
6. Do not include address or date (modern format)
7. Start with "Dear Hiring Manager," and end with "Best regards,"
8. Write in first person from the candidate's perspective

Write the cover letter:"""

    try:
        # Use Claude Sonnet for high-quality generation
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            temperature=0.7,  # Slightly creative but professional
            timeout=30.0,  # 30 second timeout
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        cover_letter = message.content[0].text.strip()

        logger.info(f"Successfully generated cover letter for user={user.id}, job={job.id}")

        # Prepare result
        result = {
            "cover_letter": cover_letter,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        # Cache the result in Redis (30-day TTL)
        cache_set(cache_key, result, ttl_seconds=TTL_30_DAYS)
        logger.info(f"Cached cover letter in Redis for 30 days")

        return {
            "cover_letter": cover_letter,
            "cached": False,
            "generated_at": result["generated_at"]
        }

    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return None


def generate_cv_highlights(
    user: User,
    job: Job,
    match: Match
) -> Optional[Dict[str, Any]]:
    """
    Generate tailored CV highlights for a job application

    Args:
        user: User object with profile information
        job: Job object with job details
        match: Match object with matching analysis

    Returns:
        Dictionary with:
        - highlights: List of tailored bullet points
        - cached: Whether result was from cache
        - generated_at: Timestamp of generation
    """
    if not client:
        logger.warning("Anthropic API key not configured, cannot generate CV highlights")
        return None

    # Build cache key
    cache_key = build_cv_highlights_key(user.id, job.id)

    # Check Redis cache first
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        logger.info(f"Redis cache hit for CV highlights: user={user.id}, job={job.id}")
        return {
            "highlights": cached_result["highlights"],
            "cached": True,
            "generated_at": cached_result["generated_at"]
        }

    logger.info(f"Redis cache miss for CV highlights: user={user.id}, job={job.id}, calling Claude Haiku")

    # Prepare data
    parsed_cv = user.preferences.get("parsed_cv", {}) if user.preferences else {}
    skills = user.skills or []
    experience_entries = parsed_cv.get("experience", [])

    # Format experience entries
    experience_text = ""
    for i, exp in enumerate(experience_entries, 1):
        experience_text += f"\n{i}. {exp.get('title', 'Position')} at {exp.get('company', 'Company')}"
        if exp.get('start_date') or exp.get('end_date'):
            experience_text += f" ({exp.get('start_date', '')} - {exp.get('end_date', 'present')})"
        if exp.get('description'):
            experience_text += f"\n   {exp.get('description')}"

    # Prepare job data
    # Note: match.reasoning contains structured analysis, match.analysis is just text
    reasoning = match.reasoning or {}
    required_skills = reasoning.get("job_requirements", {}).get("required_skills", [])
    job_description_excerpt = job.description[:500] if job.description else ""

    # Build the prompt
    prompt = f"""Extract and optimize the 3-5 most relevant experience bullet points from this candidate's CV for the target job.

CANDIDATE EXPERIENCE:{experience_text}

CANDIDATE SKILLS:
{', '.join(skills)}

TARGET JOB:
Title: {job.title}
Required Skills: {', '.join(required_skills)}
Description: {job_description_excerpt}

INSTRUCTIONS:
Return a JSON array of 3-5 bullet points that:
1. Highlight experiences directly relevant to the job requirements
2. Emphasize matching skills
3. Use strong action verbs (Led, Developed, Implemented, Managed, etc.)
4. Include metrics/results where available
5. Tailor language to match job description keywords
6. Each bullet should be 1-2 sentences maximum

Format: ["bullet point 1", "bullet point 2", ...]

Return ONLY the JSON array, no other text."""

    try:
        # Use Claude Haiku for cost-effective extraction
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            temperature=0.3,  # Low temperature for focused extraction
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
            response_text = "\n".join(lines[1:-1])
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

        # Parse JSON response
        highlights = json.loads(response_text)

        if not isinstance(highlights, list):
            logger.error(f"Expected list of highlights, got: {type(highlights)}")
            return None

        logger.info(f"Successfully generated {len(highlights)} CV highlights for user={user.id}, job={job.id}")

        # Prepare result
        result = {
            "highlights": highlights,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        # Cache the result in Redis (30-day TTL)
        cache_set(cache_key, result, ttl_seconds=TTL_30_DAYS)
        logger.info(f"Cached CV highlights in Redis for 30 days")

        return {
            "highlights": highlights,
            "cached": False,
            "generated_at": result["generated_at"]
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response was: {response_text[:200]}...")
        return None
    except Exception as e:
        logger.error(f"Error generating CV highlights: {e}")
        return None
