"""
Insights service for market skill analysis and career recommendations
"""
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
from app.models import Job, User, SkillAnalysis
from app.services.llm import extract_job_requirements

logger = logging.getLogger(__name__)


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
        normalized_skills = [s.lower().strip() for s in all_skills]

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
    normalized_user_skills = {s.lower().strip() for s in user_skills}

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
    Generate prioritized skill recommendations for user

    Args:
        user: User object
        market_skills: Market skill data
        skill_gaps: Skills user is missing
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
    recommendations = []

    # Get user's current skills (normalized)
    user_skills_normalized = {s.lower().strip() for s in (user.skills or [])}

    for skill_gap in skill_gaps:
        skill_data = market_skills.get(skill_gap)
        if not skill_data:
            continue

        frequency = skill_data["frequency"]
        avg_salary = skill_data.get("avg_salary")

        # Determine priority based on frequency and salary
        if frequency >= 20.0:
            priority = "high"
        elif frequency >= 10.0:
            priority = "medium"
        else:
            priority = "low"

        # Generate reason
        reason_parts = []
        if frequency >= 20.0:
            reason_parts.append(f"Required in {frequency:.0f}% of jobs")
        elif frequency >= 10.0:
            reason_parts.append(f"Common requirement ({frequency:.0f}% of jobs)")
        else:
            reason_parts.append(f"Growing demand ({frequency:.0f}% of jobs)")

        if avg_salary:
            reason_parts.append(f"avg salary ${avg_salary:,.0f}")

        reason = ", ".join(reason_parts)

        # Estimate learning effort (simplified heuristic)
        # This is a placeholder - could be enhanced with skill taxonomy/relationships
        learning_effort = estimate_learning_effort(skill_gap, user_skills_normalized)

        recommendations.append({
            "skill": skill_gap,
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
        user_skills: Set of user's current skills (normalized)

    Returns:
        "low" | "medium" | "high"
    """
    skill_lower = skill.lower()

    # Define related skill groups (simplified)
    skill_groups = {
        "frontend": {"react", "vue", "angular", "javascript", "typescript", "html", "css", "tailwind", "nextjs"},
        "backend": {"python", "java", "nodejs", "go", "ruby", "php", "django", "flask", "fastapi", "express"},
        "database": {"postgresql", "mysql", "mongodb", "redis", "sql", "nosql", "elasticsearch"},
        "devops": {"docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins", "ci/cd"},
        "mobile": {"react native", "flutter", "swift", "kotlin", "ios", "android"},
        "ml": {"python", "tensorflow", "pytorch", "scikit-learn", "machine learning", "deep learning", "ai"},
    }

    # Find which group(s) the skill belongs to
    skill_group = None
    for group_name, skills in skill_groups.items():
        if skill_lower in skills or any(s in skill_lower for s in skills):
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
        foundational_skills = {"javascript", "python", "sql", "html", "css", "git"}
        if skill_lower in foundational_skills:
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

    from datetime import datetime

    if analysis:
        # Update existing
        analysis.analysis_date = datetime.utcnow()
        analysis.market_skills = market_skills
        analysis.user_skills = user.skills or []
        analysis.skill_gaps = skill_gaps
        analysis.recommendations = recommendations
        analysis.jobs_analyzed = jobs_analyzed
    else:
        # Create new
        analysis = SkillAnalysis(
            user_id=user.id,
            analysis_date=datetime.utcnow(),
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
