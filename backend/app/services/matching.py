"""
Matching service for comparing user profiles with job requirements
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
from sqlalchemy.orm import Session
from app.models import User, Job, Match
from app.services.llm import extract_job_requirements

logger = logging.getLogger(__name__)


def normalize_skill(skill: str) -> str:
    """Normalize skill name for comparison (lowercase, strip whitespace)"""
    return skill.lower().strip()


def calculate_skill_match(user_skills: List[str], job_requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    Calculate skill match score and identify matches/gaps

    Args:
        user_skills: List of user's skills
        job_requirements: Extracted job requirements with required_skills and nice_to_have_skills

    Returns:
        Tuple of (score, matching_skills, missing_skills)
        - score: 0-100 representing skill match percentage
        - matching_skills: Skills user has that match job requirements
        - missing_skills: Required skills user is missing
    """
    if not user_skills:
        return 0.0, [], job_requirements.get("required_skills", [])

    # Normalize all skills
    normalized_user_skills = {normalize_skill(s) for s in user_skills}
    required_skills = [normalize_skill(s) for s in job_requirements.get("required_skills", [])]
    nice_to_have = [normalize_skill(s) for s in job_requirements.get("nice_to_have_skills", [])]

    # Find matches
    required_matches = [s for s in required_skills if s in normalized_user_skills]
    nice_to_have_matches = [s for s in nice_to_have if s in normalized_user_skills]
    missing_required = [s for s in required_skills if s not in normalized_user_skills]

    # Calculate score
    if not required_skills:
        # If no required skills specified, check nice-to-have
        if not nice_to_have:
            return 50.0, [], []  # No skills specified at all
        score = (len(nice_to_have_matches) / len(nice_to_have)) * 100
    else:
        # Weight: 80% required skills, 20% nice-to-have
        required_score = (len(required_matches) / len(required_skills)) * 80
        nice_to_have_score = (len(nice_to_have_matches) / len(nice_to_have) * 20) if nice_to_have else 0
        score = required_score + nice_to_have_score

    # Return original case for display
    matching_skills_display = [s for s in job_requirements.get("required_skills", []) + job_requirements.get("nice_to_have_skills", [])
                                if normalize_skill(s) in normalized_user_skills]
    missing_skills_display = [s for s in job_requirements.get("required_skills", [])
                               if normalize_skill(s) not in normalized_user_skills]

    return round(score, 2), matching_skills_display, missing_skills_display


def calculate_work_type_match(user_preferences: Dict[str, Any], job: Job) -> float:
    """
    Calculate match score for work type (permanent, contract, freelance, part-time)

    Returns:
        Score 0-100
    """
    preferred_types = user_preferences.get("job_types", [])

    # If no preference specified, accept all
    if not preferred_types:
        return 100.0

    # Check if job type matches preferences
    if job.job_type in preferred_types:
        return 100.0

    return 0.0


def calculate_location_match(user_preferences: Dict[str, Any], job: Job) -> float:
    """
    Calculate match score for location and remote type

    Returns:
        Score 0-100
    """
    preferred_remote = user_preferences.get("remote_types", [])
    preferred_countries = user_preferences.get("preferred_countries", [])

    remote_score = 100.0  # Default if no preference
    location_score = 100.0  # Default if no preference

    # Check remote type preference
    if preferred_remote:
        if job.remote_type in preferred_remote:
            remote_score = 100.0
        elif job.remote_type == "full" and "hybrid" in preferred_remote:
            remote_score = 80.0  # Full remote is close to hybrid
        elif job.remote_type == "hybrid" and "full" in preferred_remote:
            remote_score = 60.0  # Hybrid is somewhat acceptable for full remote seekers
        else:
            remote_score = 0.0

    # Check country/location preference
    if preferred_countries:
        job_location = (job.location or "").lower()

        # Check if "remote" is in preferences - matches any remote job
        if "remote" in [c.lower() for c in preferred_countries] and job.remote_type == "full":
            location_score = 100.0
        # Check if job location contains any preferred country
        elif any(country.lower() in job_location for country in preferred_countries):
            location_score = 100.0
        else:
            location_score = 30.0  # Partial score for location mismatch if remote-friendly

    # Average remote and location scores
    return (remote_score + location_score) / 2


def calculate_salary_match(user_preferences: Dict[str, Any], job: Job) -> float:
    """
    Calculate match score for salary expectations

    Returns:
        Score 0-100
    """
    min_salary = user_preferences.get("min_salary")

    # If no salary preference, perfect match
    if not min_salary:
        return 100.0

    # If job has no salary info, neutral score
    if not job.salary_min and not job.salary_max:
        return 50.0

    # Check if salary meets minimum
    job_max = job.salary_max or job.salary_min
    if job_max and job_max >= min_salary:
        return 100.0
    elif job.salary_min and job.salary_min >= min_salary * 0.9:
        return 80.0  # Close to minimum
    elif job.salary_min and job.salary_min >= min_salary * 0.8:
        return 60.0  # Somewhat close
    else:
        return 30.0  # Below expectations


def calculate_experience_match(user: User, job_requirements: Dict[str, Any]) -> float:
    """
    Calculate match score for experience requirements

    Returns:
        Score 0-100
    """
    user_years = user.experience_years
    min_years = job_requirements.get("experience_years_min")
    max_years = job_requirements.get("experience_years_max")

    # If no experience info, neutral score
    if not user_years or (not min_years and not max_years):
        return 50.0

    # Check if user experience falls in range
    if min_years and user_years < min_years:
        # User is under-experienced
        gap = min_years - user_years
        if gap <= 1:
            return 80.0  # Close enough
        elif gap <= 2:
            return 60.0
        else:
            return 40.0
    elif max_years and user_years > max_years:
        # User is over-experienced
        return 90.0  # Slightly penalize overqualification
    else:
        return 100.0  # Perfect match


def calculate_match_score(
    user: User,
    job: Job,
    job_requirements: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate overall match score between user and job

    Args:
        user: User object with skills and preferences
        job: Job object
        job_requirements: Extracted job requirements from LLM

    Returns:
        Tuple of (overall_score, detailed_analysis)
        - overall_score: Weighted score 0-100
        - detailed_analysis: Breakdown of scores by category
    """
    user_skills = user.skills or []
    user_prefs = user.preferences or {}

    # Calculate individual scores
    skill_score, matching_skills, missing_skills = calculate_skill_match(user_skills, job_requirements)
    work_type_score = calculate_work_type_match(user_prefs, job)
    location_score = calculate_location_match(user_prefs, job)
    salary_score = calculate_salary_match(user_prefs, job)
    experience_score = calculate_experience_match(user, job_requirements)

    # Weighted average (total = 100%)
    weights = {
        "skills": 0.45,          # 45%
        "work_type": 0.15,       # 15%
        "location": 0.15,        # 15%
        "salary": 0.10,          # 10%
        "experience": 0.15,      # 15%
    }

    overall_score = (
        skill_score * weights["skills"] +
        work_type_score * weights["work_type"] +
        location_score * weights["location"] +
        salary_score * weights["salary"] +
        experience_score * weights["experience"]
    )

    analysis = {
        "overall_score": round(overall_score, 2),
        "skill_score": round(skill_score, 2),
        "work_type_score": round(work_type_score, 2),
        "location_score": round(location_score, 2),
        "salary_score": round(salary_score, 2),
        "experience_score": round(experience_score, 2),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "weights": weights,
    }

    return round(overall_score, 2), analysis


async def create_match_for_job(
    db: Session,
    user: User,
    job: Job,
    min_score: float = 60.0
) -> Optional[Match]:
    """
    Create or update a match between user and job

    Args:
        db: Database session
        user: User object
        job: Job object
        min_score: Minimum score threshold to create match (default 60)

    Returns:
        Match object if score >= min_score, None otherwise
    """
    try:
        # Extract job requirements using LLM
        job_requirements = extract_job_requirements(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description
        )

        if not job_requirements:
            logger.warning(f"Failed to extract requirements for job {job.id}")
            return None

        # Calculate match score
        score, analysis = calculate_match_score(user, job, job_requirements)

        # Only create match if score meets threshold
        if score < min_score:
            logger.info(f"Job {job.id} score {score} below threshold {min_score} for user {user.id}")
            return None

        # Check if match already exists
        existing_match = db.query(Match).filter(
            Match.user_id == user.id,
            Match.job_id == job.id
        ).first()

        if existing_match:
            # Update existing match
            existing_match.score = score
            existing_match.reasoning = analysis
            existing_match.analysis = f"Match score: {score}/100. Skills: {len(analysis['matching_skills'])}/{len(analysis['matching_skills']) + len(analysis['missing_skills'])}"
            db.commit()
            db.refresh(existing_match)
            logger.info(f"Updated match {existing_match.id} for user {user.id} and job {job.id} with score {score}")
            return existing_match
        else:
            # Create new match
            new_match = Match(
                user_id=user.id,
                job_id=job.id,
                score=score,
                reasoning=analysis,
                analysis=f"Match score: {score}/100. Skills: {len(analysis['matching_skills'])}/{len(analysis['matching_skills']) + len(analysis['missing_skills'])}"
            )
            db.add(new_match)
            db.commit()
            db.refresh(new_match)
            logger.info(f"Created match {new_match.id} for user {user.id} and job {job.id} with score {score}")
            return new_match

    except Exception as e:
        logger.error(f"Error creating match for user {user.id} and job {job.id}: {e}")
        db.rollback()
        return None


async def match_user_with_all_jobs(
    db: Session,
    user: User,
    min_score: float = 60.0,
    limit: Optional[int] = None
) -> List[Match]:
    """
    Match a user against all jobs in the database

    Args:
        db: Database session
        user: User object
        min_score: Minimum score threshold
        limit: Optional limit on number of jobs to process

    Returns:
        List of Match objects created
    """
    # Get all jobs
    query = db.query(Job).order_by(Job.scraped_at.desc())
    if limit:
        query = query.limit(limit)

    jobs = query.all()

    matches = []
    for job in jobs:
        match = await create_match_for_job(db, user, job, min_score)
        if match:
            matches.append(match)

    logger.info(f"Created {len(matches)} matches for user {user.id} from {len(jobs)} jobs")
    return matches


async def match_job_with_all_users(
    db: Session,
    job: Job,
    min_score: float = 60.0
) -> List[Match]:
    """
    Match a job against all users in the database

    Args:
        db: Database session
        job: Job object
        min_score: Minimum score threshold

    Returns:
        List of Match objects created
    """
    # Get all active users with CV uploaded
    users = db.query(User).filter(
        User.is_active == True,
        User.cv_text.isnot(None)
    ).all()

    matches = []
    for user in users:
        match = await create_match_for_job(db, user, job, min_score)
        if match:
            matches.append(match)

    logger.info(f"Created {len(matches)} matches for job {job.id} from {len(users)} users")
    return matches
