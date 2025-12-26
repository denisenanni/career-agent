"""
Skills router - popular skills aggregation from job tags and custom skills
"""
from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List
import logging

from app.database import get_db
from app.models.job import Job
from app.models.custom_skill import CustomSkill

logger = logging.getLogger(__name__)
router = APIRouter()

# Filter out generic/non-technical terms from skill suggestions
SKILL_BLACKLIST = {
    # Generic roles
    'engineer', 'engineering', 'designer', 'design', 'developer', 'manager',
    'analyst', 'lead', 'senior', 'junior', 'intern', 'executive',

    # Generic terms
    'digital nomad', 'remote', 'freelance', 'full-time', 'part-time',
    'work from home', 'startup', 'team', 'company',

    # Too broad
    'technology', 'software', 'hardware', 'tech', 'it',

    # Locations
    'usa', 'europe', 'asia', 'america', 'worldwide',

    # Single letters (often mistakes)
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
}


@router.get("/from-jobs")
async def get_skills_from_jobs(
    search: str = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=50, le=200, ge=10),
    db: Session = Depends(get_db)
):
    """
    Get skills extracted from job postings for filter UI.

    Returns skills sorted by frequency (most common first) with job counts.
    This is optimized for the skills filter dropdown in the jobs listing.

    - **search**: Optional search term to filter skills by name (case-insensitive)
    - **limit**: Maximum number of skills to return (10-200, default 50)

    Returns list of skills with frequency count: [{"skill": "React", "count": 150}, ...]
    """
    try:
        # Get skills from job tags with frequency
        job_skills_query = text("""
            SELECT
                json_array_elements_text(tags::json) as skill,
                COUNT(*) as frequency
            FROM jobs
            WHERE tags IS NOT NULL
              AND json_array_length(tags::json) > 0
            GROUP BY skill
            ORDER BY frequency DESC
        """)

        job_result = db.execute(job_skills_query)
        job_skills = {row[0]: row[1] for row in job_result}

        # Filter out blacklisted/generic terms
        filtered_skills = {
            skill: freq for skill, freq in job_skills.items()
            if skill.lower() not in SKILL_BLACKLIST and len(skill) > 1
        }

        # If search term provided, filter by name match (case-insensitive)
        if search:
            search_lower = search.lower()
            filtered_skills = {
                skill: freq for skill, freq in filtered_skills.items()
                if search_lower in skill.lower()
            }

        # Sort by frequency and take top N
        sorted_skills = sorted(filtered_skills.items(), key=lambda x: x[1], reverse=True)[:limit]

        skills_with_count = [{"skill": skill, "count": count} for skill, count in sorted_skills]

        logger.info(f"Returning {len(skills_with_count)} skills from jobs (search={search})")

        return {
            "skills": skills_with_count
        }

    except Exception as e:
        logger.error(f"Error fetching skills from jobs: {e}")
        return {
            "skills": []
        }


@router.get("/popular")
async def get_popular_skills(
    limit: int = Query(default=200, le=500, ge=10),
    search: str = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    """
    Get most popular skills from job tags and custom user-added skills

    Aggregates all tags from jobs and merges with custom skills.
    This gives a real-time view of in-demand skills from actual job postings
    plus skills that users have added.

    - **limit**: Maximum number of skills to return (10-500, default 200)
    - **search**: Optional search term to filter skills by name (case-insensitive)

    Returns list of skills sorted by frequency (most common first)
    """
    try:
        # Get skills from job tags
        job_skills_query = text("""
            SELECT
                json_array_elements_text(tags::json) as skill,
                COUNT(*) as frequency
            FROM jobs
            WHERE tags IS NOT NULL
              AND json_array_length(tags::json) > 0
            GROUP BY skill
            ORDER BY frequency DESC
        """)

        job_result = db.execute(job_skills_query)
        job_skills = {row[0]: row[1] for row in job_result}

        # Get custom skills
        custom_skills = db.query(CustomSkill).all()
        logger.info(f"Found {len(custom_skills)} custom skills in database")
        for custom_skill in custom_skills:
            # If skill exists in job tags, add usage count to frequency
            # Otherwise, use usage count as frequency
            if custom_skill.skill in job_skills:
                job_skills[custom_skill.skill] += custom_skill.usage_count
            else:
                job_skills[custom_skill.skill] = custom_skill.usage_count
            logger.debug(f"Custom skill: {custom_skill.skill} (usage: {custom_skill.usage_count})")

        # Filter out blacklisted/generic terms
        filtered_skills = {
            skill: freq for skill, freq in job_skills.items()
            if skill.lower() not in SKILL_BLACKLIST and len(skill) > 1
        }

        # If search term provided, filter by name match (case-insensitive)
        if search:
            search_lower = search.lower()
            filtered_skills = {
                skill: freq for skill, freq in filtered_skills.items()
                if search_lower in skill.lower()
            }

        # Sort by frequency and take top N
        sorted_skills = sorted(filtered_skills.items(), key=lambda x: x[1], reverse=True)[:limit]
        skills = [skill for skill, _ in sorted_skills]

        logger.info(f"Returning {len(skills)} popular skills (job tags + custom, filtered from {len(job_skills)} total, search={search})")

        return {
            "skills": skills,
            "total": len(skills)
        }

    except Exception as e:
        logger.error(f"Error fetching popular skills: {e}")
        # Return empty list on error rather than failing
        return {
            "skills": [],
            "total": 0
        }


@router.post("/custom")
async def add_custom_skill(
    skill: str = Body(
        ...,
        embed=True,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9+#.\-\s/()]+$",  # Allow alphanumeric, +, #, ., -, spaces, /, ()
        description="Skill name (alphanumeric, spaces, and common tech chars like +, #, ., -, /, ())"
    ),
    db: Session = Depends(get_db)
):
    """
    Add a custom skill to the database

    When users add a skill that's not in job tags, save it so other users
    can discover it. Increments usage_count if skill already exists.

    - **skill**: The skill name to add (1-100 chars, alphanumeric and common tech symbols)

    Returns the skill and whether it was newly created
    """
    try:
        skill = skill.strip()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill cannot be empty after trimming whitespace"
            )

        logger.info(f"Attempting to add custom skill: {skill}")

        # Check if skill already exists (case-insensitive)
        existing_skill = db.query(CustomSkill).filter(
            func.lower(CustomSkill.skill) == skill.lower()
        ).first()

        if existing_skill:
            # Increment usage count
            existing_skill.usage_count += 1
            db.commit()
            db.refresh(existing_skill)
            logger.info(f"Incremented usage count for custom skill '{skill}': {existing_skill.usage_count}")
            return {
                "skill": existing_skill.skill,
                "created": False,
                "usage_count": existing_skill.usage_count
            }
        else:
            # Create new custom skill
            new_skill = CustomSkill(skill=skill, usage_count=1)
            db.add(new_skill)
            db.commit()
            db.refresh(new_skill)
            logger.info(f"Created new custom skill '{skill}' with ID {new_skill.id}")
            return {
                "skill": new_skill.skill,
                "created": True,
                "usage_count": 1
            }

    except Exception as e:
        logger.error(f"Error adding custom skill '{skill}': {e}", exc_info=True)
        db.rollback()
        # Return error but don't fail the request
        return {
            "error": str(e),
            "skill": skill,
            "created": False,
            "usage_count": 0
        }
