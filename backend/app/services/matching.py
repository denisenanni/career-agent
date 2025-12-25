"""
Matching service for comparing user profiles with job requirements
"""
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models import User, Job, Match
from app.services.llm import extract_job_requirements
from app.utils.skill_aliases import normalize_skill
from app.utils.skill_clusters import calculate_skill_similarity, get_related_skills

logger = logging.getLogger(__name__)

# Career category definitions for filtering irrelevant jobs
CAREER_CATEGORIES = {
    "frontend": {"react", "vue", "angular", "css", "html", "javascript", "typescript", "tailwind", "sass", "next.js", "svelte"},
    "backend": {"python", "java", "node.js", "django", "fastapi", "spring", "sql", "postgresql", "mongodb", "go", "rust", "c#", ".net", "ruby", "rails"},
    "fullstack": {"react", "node.js", "python", "javascript", "typescript", "postgresql", "next.js"},
    "mobile": {"react native", "flutter", "swift", "kotlin", "ios", "android", "xamarin"},
    "devops": {"docker", "kubernetes", "terraform", "aws", "gcp", "azure", "ci/cd", "jenkins", "gitlab", "ansible", "linux"},
    "data": {"python", "sql", "pandas", "spark", "machine learning", "tensorflow", "pytorch", "data science", "etl", "airflow", "dbt"},
    "design": {"figma", "sketch", "adobe xd", "ui", "ux", "photoshop", "illustrator", "user research", "wireframing"},
    "3d": {"blender", "maya", "zbrush", "3ds max", "cinema 4d", "unity", "unreal", "substance painter", "rigging", "3d modeling"},
    "motion": {"after effects", "premiere", "motion graphics", "animation", "cinema 4d"},
    "game": {"unity", "unreal", "godot", "c++", "game development", "game design"},
}

# Compatible category pairs (user category -> can match job category)
COMPATIBLE_CATEGORIES = {
    ("fullstack", "frontend"),
    ("fullstack", "backend"),
    ("frontend", "fullstack"),
    ("backend", "fullstack"),
    ("design", "frontend"),  # UI designers can do frontend
    ("3d", "motion"),
    ("motion", "3d"),
    ("3d", "game"),
    ("game", "3d"),
}


def infer_career_category(skills: List[str]) -> Optional[str]:
    """
    Infer user's primary career category from their skills.

    Args:
        skills: List of user's skills

    Returns:
        Primary career category string or None if no clear match
    """
    if not skills:
        return None

    skills_lower = {s.lower() for s in skills}

    # Score each category by skill overlap
    scores: Dict[str, int] = {}
    for category, category_skills in CAREER_CATEGORIES.items():
        overlap = len(skills_lower & category_skills)
        if overlap > 0:
            scores[category] = overlap

    if not scores:
        return None

    # Return category with highest overlap
    return max(scores, key=scores.get)


def infer_job_category(job_title: str, job_skills: List[str]) -> Optional[str]:
    """
    Infer job's career category from title and required skills.

    Args:
        job_title: Job title string
        job_skills: List of required skills

    Returns:
        Job category string or None if no clear match
    """
    # First try to infer from skills
    category = infer_career_category(job_skills)
    if category:
        return category

    # Fall back to job title keywords
    title_lower = job_title.lower()
    title_keywords = {
        "frontend": ["frontend", "front-end", "front end", "ui developer", "react developer", "vue developer"],
        "backend": ["backend", "back-end", "back end", "server", "api developer", "python developer", "java developer"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
        "mobile": ["mobile", "ios", "android", "react native", "flutter"],
        "devops": ["devops", "sre", "site reliability", "infrastructure", "platform engineer", "cloud engineer"],
        "data": ["data engineer", "data scientist", "ml engineer", "machine learning", "analytics"],
        "design": ["designer", "ux", "ui/ux", "product design"],
        "3d": ["3d artist", "3d modeler", "character artist", "environment artist"],
        "motion": ["motion", "animator", "video editor"],
        "game": ["game developer", "game programmer", "game designer"],
    }

    for category, keywords in title_keywords.items():
        if any(kw in title_lower for kw in keywords):
            return category

    return None


def categories_compatible(user_category: str, job_category: str) -> bool:
    """
    Check if user's career category is compatible with job category.

    Args:
        user_category: User's inferred career category
        job_category: Job's inferred career category

    Returns:
        True if categories are compatible, False otherwise
    """
    # Same category is always compatible
    if user_category == job_category:
        return True

    # Check explicit compatibility pairs
    return (user_category, job_category) in COMPATIBLE_CATEGORIES


def should_match_career_category(
    user_skills: List[str],
    job_title: str,
    job_skills: List[str]
) -> bool:
    """
    Hard filter: Check if job's career category matches user's profile.

    This prevents clearly irrelevant matches like:
    - 3D artist getting Python backend jobs
    - Designer getting DevOps jobs

    Args:
        user_skills: User's skills list
        job_title: Job title
        job_skills: Job's required skills

    Returns:
        True if job should be considered, False to skip
    """
    user_category = infer_career_category(user_skills)
    job_category = infer_job_category(job_title, job_skills)

    # If we can't infer either category, allow the match
    if not user_category or not job_category:
        return True

    # Check compatibility
    if categories_compatible(user_category, job_category):
        return True

    logger.info(f"Category mismatch: user is '{user_category}', job is '{job_category}'")
    return False


def calculate_skill_match_ratio(user_skills: List[str], job_skills: List[str]) -> Tuple[float, int, int]:
    """
    Calculate the ratio of matched skills to required skills.

    Args:
        user_skills: User's skills
        job_skills: Job's required skills

    Returns:
        Tuple of (match_ratio, matched_count, total_required)
    """
    if not job_skills:
        return 0.0, 0, 0

    user_skills_lower = {normalize_skill(s) for s in user_skills}
    job_skills_lower = {normalize_skill(s) for s in job_skills}

    # Count exact matches
    matched = user_skills_lower & job_skills_lower

    # Also count semantic matches (via skill clusters)
    for job_skill in job_skills_lower - matched:
        for user_skill in user_skills_lower:
            similarity = calculate_skill_similarity(user_skill, job_skill)
            if similarity >= 0.5:  # Related skill
                matched.add(job_skill)
                break

    match_ratio = len(matched) / len(job_skills_lower) if job_skills_lower else 0.0
    return match_ratio, len(matched), len(job_skills_lower)


def should_match_minimum_skills(
    user_skills: List[str],
    job_skills: List[str],
    min_ratio: float = 0.2
) -> bool:
    """
    Hard filter: Require minimum skill overlap ratio.

    For jobs with 3+ required skills, require at least 20% match.
    For jobs with fewer skills, require at least 1 match.

    Args:
        user_skills: User's skills
        job_skills: Job's required skills
        min_ratio: Minimum match ratio (default 0.2 = 20%)

    Returns:
        True if minimum skill overlap is met, False otherwise
    """
    if not job_skills:
        return True  # No requirements = accept all

    match_ratio, matched_count, total_required = calculate_skill_match_ratio(user_skills, job_skills)

    # For jobs with 3+ skills, require 20% match
    if total_required >= 3:
        if match_ratio < min_ratio:
            logger.info(f"Skill ratio {match_ratio:.1%} below threshold {min_ratio:.0%} ({matched_count}/{total_required})")
            return False

    # For jobs with 1-2 skills, require at least 1 match
    elif matched_count == 0:
        logger.info(f"No skill overlap (0/{total_required})")
        return False

    return True


def calculate_skill_match(user_skills: List[str], job_requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str], List[str]]:
    """
    Calculate skill match score with semantic matching (skill clusters).

    Uses both exact matches and related skill matches:
    - Exact match = 100% credit
    - Related skill (same cluster) = 50% credit

    Args:
        user_skills: List of user's skills
        job_requirements: Extracted job requirements with required_skills and nice_to_have_skills

    Returns:
        Tuple of (score, matching_skills, missing_skills, related_skills)
        - score: 0-100 representing skill match percentage
        - matching_skills: Skills user has that exactly match
        - missing_skills: Required skills user is missing (no exact or related match)
        - related_skills: Skills matched via cluster relationship
    """
    if not user_skills:
        return 0.0, [], job_requirements.get("required_skills", []), []

    # Normalize all skills
    normalized_user_skills = {normalize_skill(s) for s in user_skills}
    required_skills = [normalize_skill(s) for s in job_requirements.get("required_skills", [])]
    nice_to_have = [normalize_skill(s) for s in job_requirements.get("nice_to_have_skills", [])]

    # Calculate semantic score for required skills
    required_exact_matches = []
    required_related_matches = []
    required_missing = []
    required_total_score = 0.0

    for req_skill in required_skills:
        best_similarity = 0.0
        matched_by = None

        for user_skill in normalized_user_skills:
            similarity = calculate_skill_similarity(user_skill, req_skill)
            if similarity > best_similarity:
                best_similarity = similarity
                matched_by = user_skill

        if best_similarity == 1.0:
            required_exact_matches.append(req_skill)
            required_total_score += 1.0
        elif best_similarity >= 0.5:
            required_related_matches.append(req_skill)
            required_total_score += 0.5
        else:
            required_missing.append(req_skill)

    # Calculate semantic score for nice-to-have skills
    nice_to_have_score = 0.0
    if nice_to_have:
        for nth_skill in nice_to_have:
            best_similarity = 0.0
            for user_skill in normalized_user_skills:
                similarity = calculate_skill_similarity(user_skill, nth_skill)
                if similarity > best_similarity:
                    best_similarity = similarity
            nice_to_have_score += best_similarity

    # Calculate final score
    if not required_skills:
        if not nice_to_have:
            return 50.0, [], [], []  # No skills specified
        score = (nice_to_have_score / len(nice_to_have)) * 100
    else:
        # Weight: 80% required skills, 20% nice-to-have
        required_pct = (required_total_score / len(required_skills)) * 80
        nice_pct = (nice_to_have_score / len(nice_to_have) * 20) if nice_to_have else 0
        score = required_pct + nice_pct

    # Return original case for display
    matching_skills_display = [s for s in job_requirements.get("required_skills", []) + job_requirements.get("nice_to_have_skills", [])
                                if normalize_skill(s) in normalized_user_skills]
    missing_skills_display = [s for s in job_requirements.get("required_skills", [])
                               if normalize_skill(s) in required_missing]
    related_skills_display = [s for s in job_requirements.get("required_skills", [])
                               if normalize_skill(s) in required_related_matches]

    return round(score, 2), matching_skills_display, missing_skills_display, related_skills_display


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


def should_match_remote_type(user_preferences: Dict[str, Any], job: Job) -> bool:
    """
    Hard filter: Check if job's remote type matches user preferences.

    Remote type is treated as a filter (not a weighted score) because:
    - Jobs are already filtered by remote type in the UI
    - User can specify remote preferences upfront
    - No point in showing jobs that don't match remote preference

    Returns:
        True if job should be matched, False to skip this job entirely
    """
    preferred_remote = user_preferences.get("remote_types", [])

    # If no preference specified, accept all
    if not preferred_remote:
        return True

    # Strict match: job must match one of the preferred remote types
    return job.remote_type in preferred_remote


def should_match_eligibility(user_preferences: Dict[str, Any], job: Job) -> bool:
    """
    Hard filter: Check if job's employment eligibility matches user's location and visa needs.

    Employment eligibility is treated as a hard filter because:
    - User cannot apply to jobs they're not eligible for
    - Legal restrictions on employment by region
    - Visa sponsorship is a critical requirement

    Returns:
        True if job should be matched, False to skip this job entirely
    """
    user_regions = user_preferences.get("eligible_regions", [])
    user_needs_visa = user_preferences.get("needs_visa_sponsorship", False)

    # 1. Check regional eligibility
    if user_regions:
        job_regions = job.eligible_regions or ["Worldwide"]

        # If job accepts worldwide, user is eligible
        if "Worldwide" in job_regions:
            pass  # Continue to visa check
        # If user can work worldwide, they're eligible for any job
        elif "Worldwide" in user_regions:
            pass  # Continue to visa check
        # Check if there's overlap between user regions and job regions
        else:
            user_regions_lower = [r.lower() for r in user_regions]
            job_regions_lower = [r.lower() for r in job_regions]
            if not any(ur in job_regions_lower for ur in user_regions_lower):
                logger.info(f"Job {job.id} regions {job_regions} don't match user regions {user_regions}")
                return False

    # 2. Check visa sponsorship requirement
    if user_needs_visa:
        # NULL means not specified - assume it might be available, so allow match
        # 0 means explicitly no sponsorship - skip this job
        # 1 means yes - allow match
        if job.visa_sponsorship == 0:
            logger.info(f"Job {job.id} doesn't offer visa sponsorship but user needs it")
            return False

    return True


def detect_job_seniority(job_title: str, experience_min: Optional[int] = None) -> str:
    """
    Detect job seniority level from title and experience requirements.

    Args:
        job_title: Job title string
        experience_min: Minimum experience years required (if known)

    Returns:
        "junior", "mid", or "senior"
    """
    title_lower = job_title.lower()

    junior_keywords = ["junior", "jr", "entry", "associate", "graduate", "intern", "trainee"]
    senior_keywords = ["senior", "sr", "lead", "principal", "staff", "head", "director", "vp", "chief"]

    # Check title keywords first (most reliable)
    if any(kw in title_lower for kw in junior_keywords):
        return "junior"
    if any(kw in title_lower for kw in senior_keywords):
        return "senior"

    # Fall back to experience requirements
    if experience_min is not None:
        if experience_min >= 5:
            return "senior"
        elif experience_min <= 2:
            return "junior"

    return "mid"


def should_match_seniority(user_preferences: Dict[str, Any], job: Job, job_requirements: Dict[str, Any]) -> bool:
    """
    Hard filter: Check if job seniority matches user's preferred level.

    Args:
        user_preferences: User preferences dict
        job: Job object
        job_requirements: Extracted job requirements

    Returns:
        True if job should be matched, False to skip
    """
    user_seniority = user_preferences.get("seniority_filter")

    # No filter = accept all
    if not user_seniority:
        return True

    job_seniority = detect_job_seniority(
        job.title,
        job_requirements.get("experience_years_min")
    )

    return job_seniority == user_seniority


def calculate_freshness_score(job: Job) -> float:
    """
    Calculate score based on job posting age.

    Gentle decay curve:
    - 0-7 days: 100%
    - 7-14 days: 95%
    - 14-30 days: 85%
    - 30+ days: 70%

    Args:
        job: Job object

    Returns:
        Score 0-100
    """
    # Use posted_at if available, fall back to scraped_at or created_at
    posted = job.posted_at or job.scraped_at or job.created_at

    if not posted:
        return 85.0  # Unknown age, assume moderate

    # Ensure posted is timezone-aware
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_old = (now - posted).days

    if days_old <= 7:
        return 100.0
    elif days_old <= 14:
        return 95.0
    elif days_old <= 30:
        return 85.0
    else:
        return 70.0


def calculate_location_match(user_preferences: Dict[str, Any], job: Job) -> float:
    """
    Calculate match score for location/country preference only.

    Note: remote_type is now handled as a hard filter (see should_match_remote_type)

    Returns:
        Score 0-100
    """
    preferred_countries = user_preferences.get("preferred_countries", [])

    # If no country preference, perfect match
    if not preferred_countries:
        return 100.0

    job_location = (job.location or "").lower()

    # Check if "remote" is in preferences - matches any remote job
    if "remote" in [c.lower() for c in preferred_countries] and job.remote_type == "full":
        return 100.0

    # Check if job location contains any preferred country
    if any(country.lower() in job_location for country in preferred_countries):
        return 100.0

    # Location mismatch
    return 30.0


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


def calculate_title_match(user: User, job: Job) -> float:
    """
    Calculate match score for job title relevance

    Uses user's target roles (from preferences) or infers from CV work history.
    Prevents irrelevant matches (e.g., "Director" for ICs, "People Ops" for developers).

    Returns:
        Score 0-100
    """
    job_title_lower = job.title.lower()

    # 1. Check if user specified target roles in preferences
    user_prefs = user.preferences or {}
    target_roles = user_prefs.get("target_roles", [])

    # 2. If no target roles, infer from CV experience titles
    if not target_roles and user_prefs.get("parsed_cv"):
        parsed_cv = user_prefs["parsed_cv"]
        experience = parsed_cv.get("experience", [])
        if experience:
            # Use most recent 3 job titles
            target_roles = [exp.get("title", "") for exp in experience[:3] if exp.get("title")]

    # 3. If still no target roles, use neutral score
    if not target_roles:
        return 50.0

    # 4. Extract keywords from target roles and job title
    # Common tech role keywords
    engineer_keywords = ["engineer", "developer", "programmer", "software", "backend", "frontend", "fullstack", "full-stack", "sde"]
    senior_keywords = ["senior", "sr", "lead", "principal", "staff"]
    manager_keywords = ["manager", "director", "head", "chief", "vp", "cto", "ceo"]
    designer_keywords = ["designer", "ux", "ui", "product design"]
    data_keywords = ["data", "analyst", "scientist", "ml", "machine learning", "ai"]
    devops_keywords = ["devops", "sre", "infrastructure", "platform", "cloud"]

    # Normalize target roles
    target_roles_lower = [role.lower() for role in target_roles]
    target_roles_text = " ".join(target_roles_lower)

    # 5. Check for role category match
    user_is_engineer = any(kw in target_roles_text for kw in engineer_keywords)
    user_is_manager = any(kw in target_roles_text for kw in manager_keywords)
    user_is_designer = any(kw in target_roles_text for kw in designer_keywords)
    user_is_data = any(kw in target_roles_text for kw in data_keywords)
    user_is_devops = any(kw in target_roles_text for kw in devops_keywords)

    job_is_engineer = any(kw in job_title_lower for kw in engineer_keywords)
    job_is_manager = any(kw in job_title_lower for kw in manager_keywords)
    job_is_designer = any(kw in job_title_lower for kw in designer_keywords)
    job_is_data = any(kw in job_title_lower for kw in data_keywords)
    job_is_devops = any(kw in job_title_lower for kw in devops_keywords)

    # 6. Calculate score based on role category alignment
    score = 0.0

    # Strong mismatch penalties
    if user_is_engineer and job_is_manager and not job_is_engineer:
        # IC engineer shouldn't match pure management roles
        return 10.0
    if user_is_manager and not job_is_manager:
        # Manager shouldn't match pure IC roles (unless it's also management)
        return 30.0

    # Category matches
    if user_is_engineer and job_is_engineer:
        score = 90.0
    elif user_is_designer and job_is_designer:
        score = 90.0
    elif user_is_data and job_is_data:
        score = 90.0
    elif user_is_devops and job_is_devops:
        score = 90.0
    elif user_is_manager and job_is_manager:
        score = 90.0
    else:
        # Check for keyword overlap
        target_words = set(target_roles_text.split())
        job_words = set(job_title_lower.split())
        overlap = target_words.intersection(job_words)

        if len(overlap) >= 2:
            score = 70.0  # Good keyword overlap
        elif len(overlap) == 1:
            score = 50.0  # Some overlap
        else:
            score = 20.0  # No clear match

    # 7. Seniority alignment bonus/penalty
    user_is_senior = any(kw in target_roles_text for kw in senior_keywords)
    job_is_senior = any(kw in job_title_lower for kw in senior_keywords)

    if user_is_senior and job_is_senior:
        score = min(100.0, score + 10.0)  # Bonus for seniority match
    elif user_is_senior and not job_is_senior:
        score = max(0.0, score - 10.0)  # Slight penalty for seniority mismatch

    return round(score, 2)


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
    skill_score, matching_skills, missing_skills, related_skills = calculate_skill_match(user_skills, job_requirements)
    title_score = calculate_title_match(user, job)
    location_score = calculate_location_match(user_prefs, job)
    salary_score = calculate_salary_match(user_prefs, job)
    experience_score = calculate_experience_match(user, job_requirements)
    freshness_score = calculate_freshness_score(job)

    # Weighted average (total = 100%)
    # Freshness added to encourage applying to recent jobs
    weights = {
        "skills": 0.35,          # 35% (reduced from 40% to add freshness)
        "title": 0.20,           # 20% (prevents "Director" for ICs)
        "location": 0.10,        # 10%
        "salary": 0.10,          # 10%
        "experience": 0.15,      # 15% (reduced from 20% to add freshness)
        "freshness": 0.10,       # 10% (NEW - encourages recent jobs)
    }

    overall_score = (
        skill_score * weights["skills"] +
        title_score * weights["title"] +
        location_score * weights["location"] +
        salary_score * weights["salary"] +
        experience_score * weights["experience"] +
        freshness_score * weights["freshness"]
    )

    analysis = {
        "overall_score": round(overall_score, 2),
        "skill_score": round(skill_score, 2),
        "title_score": round(title_score, 2),
        "location_score": round(location_score, 2),
        "salary_score": round(salary_score, 2),
        "experience_score": round(experience_score, 2),
        "freshness_score": round(freshness_score, 2),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "related_skills": related_skills,
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
        # Feedback loop: Skip if user already rejected/hidden this job
        existing_rejected = db.query(Match).filter(
            Match.user_id == user.id,
            Match.job_id == job.id,
            Match.status.in_(["rejected", "hidden"])
        ).first()
        if existing_rejected:
            logger.debug(f"Skipping job {job.id} - user {user.id} already {existing_rejected.status} it")
            return None

        # Hard filters: Check preferences first (before expensive LLM call)
        user_prefs = user.preferences or {}

        # Filter by remote type
        if not should_match_remote_type(user_prefs, job):
            logger.info(f"Job {job.id} remote_type '{job.remote_type}' doesn't match user {user.id} preferences")
            return None

        # Filter by employment eligibility
        if not should_match_eligibility(user_prefs, job):
            logger.info(f"Job {job.id} doesn't match user {user.id} eligibility requirements")
            return None

        # Extract job requirements using LLM
        job_requirements = extract_job_requirements(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description
        )

        if not job_requirements:
            logger.warning(f"Failed to extract requirements for job {job.id}")
            return None

        # Hard filter: Skip jobs with no skills extracted (likely poor job description)
        required_skills = job_requirements.get("required_skills", [])
        nice_to_have_skills = job_requirements.get("nice_to_have_skills", [])
        if not required_skills and not nice_to_have_skills:
            logger.info(f"Job {job.id} has no skills extracted - skipping")
            return None

        # Save eligibility data to Job table if extracted and not already set
        if job.eligible_regions is None and job_requirements.get("eligible_regions"):
            job.eligible_regions = job_requirements["eligible_regions"]
            db.add(job)
            db.flush()  # Update job without committing yet

        if job.visa_sponsorship is None and job_requirements.get("visa_sponsorship") is not None:
            # Convert boolean to int (0/1) or keep None
            visa_value = job_requirements["visa_sponsorship"]
            if isinstance(visa_value, bool):
                job.visa_sponsorship = 1 if visa_value else 0
            db.add(job)
            db.flush()  # Update job without committing yet

        # Seniority filter: Check after LLM extraction (needs experience_years_min)
        if not should_match_seniority(user_prefs, job, job_requirements):
            job_seniority = detect_job_seniority(job.title, job_requirements.get("experience_years_min"))
            logger.info(f"Job {job.id} seniority '{job_seniority}' doesn't match user {user.id} preference '{user_prefs.get('seniority_filter')}'")
            return None

        # Hard filter: Career category mismatch (e.g., 3D artist vs backend job)
        user_skills = user.skills or []
        if not should_match_career_category(user_skills, job.title, required_skills):
            logger.info(f"Job {job.id} career category doesn't match user {user.id} profile - skipping")
            return None

        # Hard filter: Minimum skill overlap (20% for jobs with 3+ skills)
        if not should_match_minimum_skills(user_skills, required_skills):
            logger.info(f"Job {job.id} below minimum skill overlap for user {user.id} - skipping")
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
    # Pre-filter: Get job IDs user has rejected/hidden (to exclude from matching)
    rejected_job_ids = db.query(Match.job_id).filter(
        Match.user_id == user.id,
        Match.status.in_(["rejected", "hidden"])
    ).all()
    rejected_ids = {r[0] for r in rejected_job_ids}

    # Get all jobs, excluding rejected ones
    query = db.query(Job).order_by(Job.scraped_at.desc())
    if rejected_ids:
        query = query.filter(~Job.id.in_(rejected_ids))
    if limit:
        query = query.limit(limit)

    jobs = query.all()

    matches = []
    for job in jobs:
        match = await create_match_for_job(db, user, job, min_score)
        if match:
            matches.append(match)

    logger.info(f"Created {len(matches)} matches for user {user.id} from {len(jobs)} jobs (excluded {len(rejected_ids)} rejected)")
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
