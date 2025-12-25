"""
Insights service for market skill analysis and career recommendations
"""
from typing import Dict, List, Any, Optional, Set
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
from app.models import Job, User, SkillAnalysis
from app.services.llm import extract_job_requirements
from app.utils.skill_aliases import normalize_skill
from app.services.matching import infer_career_category, CAREER_CATEGORIES

logger = logging.getLogger(__name__)

# Skill relationship paths: maps skills to commonly paired skills
# These are based on typical career progressions and complementary technologies
SKILL_PATHS = {
    # Frontend paths
    "react": ["typescript", "next.js", "redux", "tailwind css", "testing library", "jest", "graphql"],
    "vue": ["typescript", "nuxt", "vuex", "pinia", "vite"],
    "angular": ["typescript", "rxjs", "ngrx", "jasmine"],
    "javascript": ["typescript", "react", "node.js", "webpack"],
    "typescript": ["react", "node.js", "next.js", "graphql"],
    "html": ["css", "javascript", "react", "accessibility"],
    "css": ["tailwind css", "sass", "css-in-js", "responsive design"],
    "tailwind css": ["react", "next.js", "headless ui"],
    "next.js": ["react", "typescript", "vercel", "prisma"],

    # Backend paths
    "python": ["fastapi", "django", "postgresql", "redis", "docker", "aws", "celery"],
    "fastapi": ["python", "postgresql", "docker", "sqlalchemy", "pydantic"],
    "django": ["python", "postgresql", "celery", "redis", "docker"],
    "node.js": ["typescript", "express", "postgresql", "mongodb", "docker", "graphql"],
    "java": ["spring boot", "hibernate", "postgresql", "kafka", "kubernetes", "maven"],
    "go": ["docker", "kubernetes", "postgresql", "grpc", "microservices"],
    "ruby": ["rails", "postgresql", "redis", "sidekiq"],
    "postgresql": ["sql", "redis", "docker", "data modeling"],
    "mongodb": ["node.js", "mongoose", "redis"],

    # DevOps paths
    "docker": ["kubernetes", "terraform", "ci/cd", "aws", "linux"],
    "kubernetes": ["docker", "helm", "istio", "prometheus", "gitops", "terraform"],
    "aws": ["terraform", "cloudformation", "lambda", "ecs", "docker"],
    "terraform": ["aws", "azure", "gcp", "ansible", "infrastructure as code"],
    "ci/cd": ["github actions", "gitlab ci", "jenkins", "docker"],

    # Data paths
    "pandas": ["python", "sql", "numpy", "data analysis", "jupyter"],
    "sql": ["postgresql", "data modeling", "dbt", "analytics"],
    "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "deep learning"],
    "tensorflow": ["python", "keras", "deep learning", "mlops"],
    "pytorch": ["python", "deep learning", "nlp", "computer vision"],
    "spark": ["python", "sql", "airflow", "databricks", "scala"],

    # Design paths
    "figma": ["prototyping", "design systems", "user research", "adobe xd"],
    "ui": ["figma", "design systems", "accessibility", "motion design", "css"],
    "ux": ["user research", "usability testing", "wireframing", "prototyping", "figma"],
    "adobe xd": ["figma", "prototyping", "illustrator"],

    # 3D paths
    "blender": ["substance painter", "zbrush", "unity", "unreal", "rigging", "3d modeling"],
    "maya": ["zbrush", "substance painter", "rigging", "animation", "3d modeling"],
    "zbrush": ["maya", "blender", "substance painter", "sculpting"],
    "unity": ["c#", "shader programming", "vfx", "game development", "ar/vr"],
    "unreal": ["blueprints", "c++", "vfx", "game development", "nanite", "lumen"],
    "substance painter": ["blender", "maya", "texturing", "pbr"],

    # Motion/Video paths
    "after effects": ["premiere", "cinema 4d", "illustrator", "motion graphics"],
    "premiere": ["after effects", "davinci resolve", "video editing"],
    "cinema 4d": ["after effects", "3d motion", "octane render"],
    "animation": ["rigging", "character animation", "storyboarding", "blender", "maya"],

    # Mobile paths
    "react native": ["typescript", "react", "redux", "expo"],
    "flutter": ["dart", "firebase", "mobile development"],
    "swift": ["ios", "xcode", "swiftui", "uikit"],
    "kotlin": ["android", "jetpack compose", "coroutines"],
}

# Category labels for UI display
CATEGORY_LABELS = {
    "frontend": "Frontend Development",
    "backend": "Backend Development",
    "fullstack": "Full-Stack Development",
    "mobile": "Mobile Development",
    "devops": "DevOps & Infrastructure",
    "data": "Data & Machine Learning",
    "design": "UI/UX Design",
    "3d": "3D Art & Modeling",
    "motion": "Motion Graphics & Animation",
    "game": "Game Development",
}


def get_related_skills_for_user(user_skills: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Find skills that are related to the user's existing skills.

    This is the core of profile-aware recommendations:
    - Only suggest skills that build on what user already knows
    - If user has no skills in SKILL_PATHS, return empty (no generic suggestions)

    Args:
        user_skills: List of user's current skills

    Returns:
        Dictionary of related skills with metadata:
        {
            "skill": {
                "source_skill": str,  # Which user skill this relates to
                "reason": str,        # Why this is recommended
            }
        }
    """
    if not user_skills:
        return {}

    user_skills_lower = {s.lower() for s in user_skills}
    related_skills: Dict[str, Dict[str, Any]] = {}

    for user_skill in user_skills_lower:
        # Check if this skill has related skills defined
        if user_skill in SKILL_PATHS:
            for related in SKILL_PATHS[user_skill]:
                related_lower = related.lower()
                # Skip if user already has this skill
                if related_lower in user_skills_lower:
                    continue
                # Skip if we already found this skill from another source
                if related_lower in related_skills:
                    continue

                related_skills[related_lower] = {
                    "source_skill": user_skill,
                    "reason": f"Commonly paired with {user_skill}",
                    "original_name": related,  # Preserve original casing
                }

    return related_skills


def analyze_market_skills(db: Session, limit: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """
    Analyze skills across all jobs to identify market trends

    Args:
        db: Database session
        limit: Optional limit on number of jobs to analyze

    Returns:
        Dictionary mapping skill names to their market data:
        {
            "skill_name": {
                "count": int,           # Number of jobs requiring this skill
                "frequency": float,     # Percentage of jobs (0-100)
                "avg_salary": float,    # Average salary for jobs with this skill
                "jobs_with_salary": int # Number of jobs with salary data
            }
        }
    """
    # Get all jobs
    query = db.query(Job).order_by(Job.scraped_at.desc())
    if limit:
        query = query.limit(limit)

    jobs = query.all()

    if not jobs:
        logger.warning("No jobs found for market analysis")
        return {}

    # Aggregate skills
    skill_counter = Counter()
    skill_salaries = {}  # skill -> list of salaries

    for job in jobs:
        # Extract requirements for this job
        requirements = extract_job_requirements(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description
        )

        if not requirements:
            continue

        # Get all skills (required + nice-to-have)
        required_skills = requirements.get("required_skills") or []
        nice_to_have_skills = requirements.get("nice_to_have_skills") or []
        all_skills = required_skills + nice_to_have_skills

        # Normalize and count
        normalized_skills = [normalize_skill(s) for s in all_skills]

        for skill in normalized_skills:
            skill_counter[skill] += 1

            # Track salary data
            if job.salary_max:
                if skill not in skill_salaries:
                    skill_salaries[skill] = []
                skill_salaries[skill].append(job.salary_max)

    # Calculate statistics
    total_jobs = len(jobs)
    market_data = {}

    for skill, count in skill_counter.items():
        frequency = (count / total_jobs) * 100

        # Calculate average salary
        avg_salary = None
        jobs_with_salary = 0
        if skill in skill_salaries:
            salaries = skill_salaries[skill]
            avg_salary = sum(salaries) / len(salaries)
            jobs_with_salary = len(salaries)

        market_data[skill] = {
            "count": count,
            "frequency": round(frequency, 2),
            "avg_salary": round(avg_salary, 2) if avg_salary else None,
            "jobs_with_salary": jobs_with_salary,
        }

    logger.info(f"Analyzed {total_jobs} jobs, found {len(market_data)} unique skills")
    return market_data


def identify_skill_gaps(user_skills: List[str], market_skills: Dict[str, Dict[str, Any]], min_frequency: float = 5.0) -> List[str]:
    """
    Identify skills that are in demand but user doesn't have

    Args:
        user_skills: List of user's current skills
        market_skills: Market skill data from analyze_market_skills
        min_frequency: Minimum frequency percentage to consider (default 5%)

    Returns:
        List of skill names user is missing
    """
    # Normalize user skills
    normalized_user_skills = {normalize_skill(s) for s in user_skills}

    # Find gaps
    gaps = []
    for skill, data in market_skills.items():
        # Skip if user already has this skill
        if skill in normalized_user_skills:
            continue

        # Only include skills that appear in >= min_frequency of jobs
        if data["frequency"] >= min_frequency:
            gaps.append(skill)

    return gaps


def generate_skill_recommendations(
    user: User,
    market_skills: Dict[str, Dict[str, Any]],
    skill_gaps: List[str],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate prioritized skill recommendations for user.

    IMPORTANT: Recommendations are based PRIMARILY on user's existing skills.
    If the user has no skills that map to known skill paths, return an empty list
    rather than generic market-based suggestions.

    Args:
        user: User object
        market_skills: Market skill data
        skill_gaps: Skills user is missing (market-wide)
        top_n: Number of top recommendations to return

    Returns:
        List of recommendations, each with:
        {
            "skill": str,
            "priority": "high" | "medium" | "low",
            "reason": str,
            "frequency": float,
            "salary_impact": float or None,
            "learning_effort": "low" | "medium" | "high"
        }
    """
    user_skills = user.skills or []
    if not user_skills:
        logger.info("User has no skills - cannot generate profile-aware recommendations")
        return []

    # Get skills related to user's existing skills
    related_skills = get_related_skills_for_user(user_skills)

    if not related_skills:
        # User has skills but none of them are in our skill paths
        # This means we can't suggest anything relevant to their profile
        logger.info(f"No related skills found for user's skills: {user_skills}")
        return []

    recommendations = []
    user_skills_normalized = {normalize_skill(s) for s in user_skills}

    # Only recommend skills that are:
    # 1. Related to user's existing skills (from SKILL_PATHS)
    # 2. Have market demand (appear in job postings)
    for skill_key, skill_info in related_skills.items():
        # Check if this skill appears in the market
        skill_data = market_skills.get(skill_key)

        # If not in market data, still include but with lower priority
        frequency = skill_data["frequency"] if skill_data else 0.0
        avg_salary = skill_data.get("avg_salary") if skill_data else None

        # Determine priority:
        # - Related skills that are in high demand = high priority
        # - Related skills with some demand = medium priority
        # - Related skills with low/no market data = low priority (still relevant to user's path)
        if frequency >= 15.0:
            priority = "high"
        elif frequency >= 5.0:
            priority = "medium"
        else:
            priority = "low"

        # Generate reason - emphasize the relationship to user's skills
        reason_parts = [skill_info["reason"]]
        if frequency >= 10.0:
            reason_parts.append(f"in demand ({frequency:.0f}% of jobs)")
        elif frequency >= 5.0:
            reason_parts.append(f"growing demand ({frequency:.0f}% of jobs)")

        if avg_salary:
            reason_parts.append(f"avg ${avg_salary:,.0f}")

        reason = ", ".join(reason_parts)

        # Estimate learning effort
        learning_effort = estimate_learning_effort(skill_key, user_skills_normalized)

        recommendations.append({
            "skill": skill_info.get("original_name", skill_key),
            "priority": priority,
            "reason": reason,
            "frequency": frequency,
            "salary_impact": avg_salary,
            "learning_effort": learning_effort,
        })

    # Sort by priority (high first), then frequency
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: (priority_order[x["priority"]], -x["frequency"]))

    return recommendations[:top_n]


def estimate_learning_effort(skill: str, user_skills: set) -> str:
    """
    Estimate learning effort for a skill based on user's existing skills

    This is a simplified heuristic. In production, this could use:
    - Skill taxonomy/ontology
    - Machine learning model
    - External skill relationship data

    Args:
        skill: Skill to learn
        user_skills: Set of user's current skills (normalized/canonical)

    Returns:
        "low" | "medium" | "high"
    """
    # Normalize the skill to canonical form
    skill_normalized = normalize_skill(skill)

    # Define related skill groups using canonical names
    skill_groups = {
        "frontend": {"React", "Vue", "Angular", "JavaScript", "TypeScript", "HTML", "CSS", "Tailwind CSS", "Next.js"},
        "backend": {"Python", "Java", "Node.js", "Go", "Ruby", "PHP", "Django", "Flask", "FastAPI", "Express"},
        "database": {"PostgreSQL", "MySQL", "MongoDB", "Redis", "SQL", "Elasticsearch"},
        "devops": {"Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "Terraform", "Ansible", "Jenkins", "CI/CD"},
        "mobile": {"React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android"},
        "ml": {"Python", "TensorFlow", "PyTorch", "scikit-learn", "Machine Learning", "Deep Learning", "AI"},
    }

    # Find which group(s) the skill belongs to
    skill_group = None
    for group_name, skills in skill_groups.items():
        if skill_normalized in skills:
            skill_group = group_name
            break

    if not skill_group:
        # Unknown skill, assume medium effort
        return "medium"

    # Check if user has related skills
    related_skills = skill_groups[skill_group]
    has_related = any(user_skill in related_skills for user_skill in user_skills)

    if has_related:
        # User has related skills, easier to learn
        return "low"
    else:
        # User doesn't have related skills
        # Check if it's a foundational skill
        foundational_skills = {"JavaScript", "Python", "SQL", "HTML", "CSS", "Git"}
        if skill_normalized in foundational_skills:
            return "medium"
        else:
            return "high"


def create_or_update_skill_analysis(
    db: Session,
    user: User,
    market_skills: Dict[str, Dict[str, Any]],
    skill_gaps: List[str],
    recommendations: List[Dict[str, Any]],
    jobs_analyzed: int
) -> SkillAnalysis:
    """
    Create or update skill analysis for user

    Args:
        db: Database session
        user: User object
        market_skills: Market skill data
        skill_gaps: Skill gaps identified
        recommendations: Generated recommendations
        jobs_analyzed: Number of jobs analyzed

    Returns:
        SkillAnalysis object
    """
    # Check if analysis exists
    analysis = db.query(SkillAnalysis).filter(SkillAnalysis.user_id == user.id).first()

    from datetime import datetime, timezone

    if analysis:
        # Update existing
        analysis.analysis_date = datetime.now(timezone.utc)
        analysis.market_skills = market_skills
        analysis.user_skills = user.skills or []
        analysis.skill_gaps = skill_gaps
        analysis.recommendations = recommendations
        analysis.jobs_analyzed = jobs_analyzed
    else:
        # Create new
        analysis = SkillAnalysis(
            user_id=user.id,
            analysis_date=datetime.now(timezone.utc),
            market_skills=market_skills,
            user_skills=user.skills or [],
            skill_gaps=skill_gaps,
            recommendations=recommendations,
            jobs_analyzed=jobs_analyzed,
        )
        db.add(analysis)

    db.commit()
    db.refresh(analysis)

    logger.info(f"Updated skill analysis for user {user.id}: {len(skill_gaps)} gaps, {len(recommendations)} recommendations")
    return analysis


def run_skill_analysis_for_user(db: Session, user: User) -> SkillAnalysis:
    """
    Run complete skill analysis for a user

    This will:
    1. Analyze market skills across all jobs
    2. Identify skill gaps for user
    3. Generate recommendations
    4. Store results in database

    Args:
        db: Database session
        user: User object

    Returns:
        SkillAnalysis object
    """
    # Analyze market
    market_skills = analyze_market_skills(db)

    # Identify gaps
    skill_gaps = identify_skill_gaps(user.skills or [], market_skills, min_frequency=5.0)

    # Generate recommendations
    recommendations = generate_skill_recommendations(user, market_skills, skill_gaps, top_n=10)

    # Get job count
    jobs_analyzed = db.query(func.count(Job.id)).scalar()

    # Save analysis
    analysis = create_or_update_skill_analysis(
        db=db,
        user=user,
        market_skills=market_skills,
        skill_gaps=skill_gaps,
        recommendations=recommendations,
        jobs_analyzed=jobs_analyzed
    )

    return analysis
