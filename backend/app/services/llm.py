"""
LLM service for CV parsing and job analysis using Claude
"""
from typing import Optional, Dict, Any
import json
import logging
from anthropic import Anthropic
from app.config import settings

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
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            temperature=0,  # Deterministic for extraction
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
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0,
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
        return parsed_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        return None
