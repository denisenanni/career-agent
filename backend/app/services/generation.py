"""
Application materials generation service using Claude

Generates personalized cover letters and CV highlights with Redis caching
to minimize API costs and provide instant responses for cached content.

IMPROVEMENTS:
- Strategic prompt engineering to prevent self-sabotage
- Concrete examples and specificity enforcement
- Better handling of skill gaps (emphasize strengths, not weaknesses)
- Professional positioning without dishonesty
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


# ============================================================================
# IMPROVED PROMPT TEMPLATES
# ============================================================================

def build_cover_letter_prompt(
    name: str,
    skills: str,
    years_exp: int,
    summary: str,
    experience_text: str,
    job_title: str,
    company_name: str,
    required_skills: str,
    job_description_excerpt: str,
    matching_skills: str,
    num_matches: int,
    match_score: float,
    skill_gaps: List[str] = None
) -> str:
    """
    Build improved cover letter prompt with strategic positioning
    
    Key improvements:
    - Prevents self-sabotaging language
    - Enforces concrete examples
    - Strategic gap handling
    - Clear DO/DON'T guidelines
    """
    
    skill_gaps = skill_gaps or []
    
    # Build skill gaps section (for context only, not to mention in letter)
    skill_gaps_section = ""
    if skill_gaps and len(skill_gaps) > 0:
        gaps_list = ', '.join(skill_gaps[:5])
        skill_gaps_section = f"\nSkills Not Currently Listed ({len(skill_gaps)}): {gaps_list}"
    
    # Build strategic guidance for handling gaps
    if not skill_gaps:
        skill_gap_strategy = "No significant skill gaps identified. Focus entirely on demonstrating matching skills with concrete examples."
    else:
        skill_gap_strategy = f"""The candidate has {len(skill_gaps)} skills not currently listed in their profile.

**Strategy for gaps:**
1. DO NOT mention specific gaps in the cover letter
2. Instead, emphasize the {num_matches} matching skills with detailed examples
3. If a missing skill has a close equivalent the candidate possesses, highlight that equivalent
4. Demonstrate adaptability through past examples of learning new technologies quickly
5. Focus on transferable skills and relevant experience

**What this means in practice:**
- If job requires PostgreSQL but candidate has MySQL/SQL Server → Emphasize database design, query optimization, and SQL expertise
- If job requires specific framework but candidate has similar → Emphasize architectural understanding and ability to work with modern frameworks
- If job requires technology candidate used 2+ years ago → Present it as experience, not as something outdated

**Never write:**
"While I haven't worked extensively with [missing skill]..."

**Instead write:**
"My experience with [related skill] includes [specific example]..."
"""

    prompt = f"""You are an expert career advisor writing a compelling cover letter for a job application.

=== CANDIDATE PROFILE ===
Name: {name}
Current Skills: {skills}
Years of Experience: {years_exp}
Professional Summary: {summary}

Relevant Experience:{experience_text}

=== TARGET POSITION ===
Position: {job_title}
Company: {company_name}
Required Skills: {required_skills}
Job Description (excerpt): {job_description_excerpt}

=== MATCH ANALYSIS ===
Matching Skills ({num_matches}): {matching_skills}
Match Score: {match_score:.0f}%{skill_gaps_section}

=== CORE WRITING PRINCIPLES ===

**Strategic Honesty:**
- Only claim skills and experience the candidate actually possesses
- Frame existing experience in the most relevant light
- DO NOT volunteer gaps or weaknesses unless specifically asked
- If a required skill is missing, emphasize closely related transferable skills instead
- Never use phrases like "I'm learning" or "I'm expanding into" for core job requirements

**Positioning Strategy:**
- Lead with strongest matches to job requirements
- Use specific examples with concrete technologies and outcomes
- Quantify impact when possible (team size, scale, metrics)
- Show genuine understanding of the company/role (reference specific details when available)

**What NOT to say:**
- ❌ "I haven't worked extensively with [required skill]"
- ❌ "I'm recently expanding into [core requirement]"
- ❌ "I lack experience in [specific area]"
- ❌ "I'm eager to learn [required skill]" (for fundamental requirements)
- ❌ Generic phrases: "various projects", "worked with", "experience in" without specifics

**What TO say:**
- ✅ "Built [specific thing] using [technology], resulting in [outcome]"
- ✅ "At [Company], [specific achievement with metrics]"
- ✅ "Demonstrated expertise in [transferable skill] through [concrete example]"
- ✅ "[Years] of production experience with [technology stack]"

=== STRUCTURE & FORMAT ===

**Opening (2-3 sentences):**
- Hook with specific insight about company/role (not generic praise)
- State the position clearly
- Brief, confident value proposition

**Body Paragraph 1 (4-5 sentences):**
- Address the top 2-3 technical requirements with CONCRETE examples
- Name specific technologies, projects, or outcomes
- Include at least one quantifiable result
- Focus on MATCHING skills from the analysis

**Body Paragraph 2 (3-4 sentences):**
- Address cultural fit, work style, or unique value propositions
- Connect candidate's approach to company needs
- Show understanding of role context (being first engineer, remote work, etc.)
- Can mention transferable skills if relevant

**Closing (2-3 sentences):**
- Express genuine (but not desperate) enthusiasm
- Clear next step
- Professional sign-off

**Hard Constraints:**
- Maximum 400 words total
- Start with "Dear Hiring Manager,"
- End with "Best regards," and name
- First person perspective
- Modern format (no address/date)
- Professional but conversational tone
- NO bullet points in the letter body

=== HANDLING SKILL GAPS ===

{skill_gap_strategy}

=== OUTPUT ===
Write the cover letter following all the principles and structure above. Be specific, confident, and genuine.

Cover letter:"""

    return prompt


def build_cv_highlights_prompt(
    experience_text: str,
    skills_list: str,
    job_title: str,
    company_name: str,
    required_skills: str,
    job_description_excerpt: str,
    matching_skills: str,
    match_score: float
) -> str:
    """
    Build improved CV highlights prompt with specificity enforcement
    
    Key improvements:
    - Bullet point formula enforcement
    - Good vs bad examples
    - Strategic positioning guidance
    - Banned vague language
    """
    
    prompt = f"""You are an expert at extracting and tailoring CV highlights for job applications.

=== CANDIDATE EXPERIENCE ===
{experience_text}

=== CANDIDATE SKILLS ===
{skills_list}

=== TARGET POSITION ===
Title: {job_title}
Company: {company_name}
Required Skills: {required_skills}
Description: {job_description_excerpt}

=== MATCH CONTEXT ===
Top Matching Skills: {matching_skills}
Match Score: {match_score:.0f}%

=== EXTRACTION PRINCIPLES ===

**Selection Criteria:**
- Choose 4-6 experiences MOST relevant to this specific job
- Prioritize recent experience over old (unless old is extremely relevant)
- Emphasize experiences that demonstrate required skills
- Include diversity of relevant skills (don't repeat the same skill 4 times)

**Bullet Point Formula:**
Each bullet MUST follow: [Action Verb] + [Specific Technology/Skill] + [Concrete Context/Outcome]

Examples of GOOD bullets:
✅ "Developed full-stack web applications using TypeScript, React, and Node.js, building scalable frontend architectures with complex state management and REST APIs"
✅ "Led migration of 50+ components from JavaScript to TypeScript, reducing runtime errors by 40% and improving developer velocity"
✅ "Implemented CI/CD pipelines using GitLab, Terraform, and Docker, automating deployments across 5 microservices"

Examples of BAD bullets:
❌ "Worked on various web development projects" (too vague)
❌ "Experience with React and TypeScript" (just listing, no action or outcome)
❌ "Helped team with DevOps tasks" (no specificity)
❌ "Familiar with modern JavaScript frameworks" (weak claim)

**Strategic Positioning:**
- If candidate has limited experience with a required skill, emphasize:
  - Related skills used in production
  - Transferable expertise
  - Similar technologies mastered
- DO NOT mention "learning", "gaining experience", or "transitioning into"
- Focus on what candidate HAS done, not what they're trying to do

**Specificity Requirements:**
- Name exact technologies (not "various tools" or "modern frameworks")
- Include scale/metrics when possible (user count, team size, performance gains)
- Use concrete verbs: Built, Developed, Implemented, Led, Architected, Designed, Deployed
- Avoid weak verbs: Worked on, Helped with, Assisted, Familiar with

**Relevance Matching:**
- Each bullet should clearly map to at least one job requirement
- Use language/terminology from the job description
- Highlight matching skills identified in the analysis
- Order bullets by relevance (most relevant first)

=== OUTPUT FORMAT ===

Return a JSON array of 4-6 bullet points following the formula above.

Requirements:
- Each bullet is 1-2 sentences maximum
- Present tense for current role, past tense for previous roles
- Specific technologies and outcomes in every bullet
- Direct relevance to job requirements
- No generic statements

Return ONLY the JSON array, nothing else.

Format: ["bullet 1", "bullet 2", "bullet 3", "bullet 4", ...]

JSON array:"""

    return prompt


# ============================================================================
# MAIN GENERATION FUNCTIONS
# ============================================================================

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
    reasoning = match.reasoning or {}
    required_skills = reasoning.get("job_requirements", {}).get("required_skills", [])
    job_description_excerpt = job.description[:500] if job.description else ""

    # Prepare match analysis
    skill_matches = reasoning.get("matching_skills", [])
    skill_gaps = reasoning.get("missing_skills", [])
    match_score = match.score or 0

    # Build the improved prompt
    prompt = build_cover_letter_prompt(
        name=name,
        skills=skills,
        years_exp=years_exp,
        summary=summary,
        experience_text=experience_text,
        job_title=job.title,
        company_name=job.company,
        required_skills=', '.join(required_skills[:10]),
        job_description_excerpt=job_description_excerpt,
        matching_skills=', '.join(skill_matches[:10]),
        num_matches=len(skill_matches),
        match_score=match_score,
        skill_gaps=skill_gaps[:5]  # Pass gaps for context, but prompt won't mention them
    )

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
    reasoning = match.reasoning or {}
    required_skills = reasoning.get("job_requirements", {}).get("required_skills", [])
    skill_matches = reasoning.get("matching_skills", [])
    job_description_excerpt = job.description[:500] if job.description else ""
    match_score = match.score or 0

    # Build the improved prompt
    prompt = build_cv_highlights_prompt(
        experience_text=experience_text,
        skills_list=', '.join(skills),
        job_title=job.title,
        company_name=job.company,
        required_skills=', '.join(required_skills),
        job_description_excerpt=job_description_excerpt,
        matching_skills=', '.join(skill_matches[:10]),
        match_score=match_score
    )

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