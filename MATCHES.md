# Matching Algorithm

This document explains how the job matching algorithm works.

## Overview

The matching system uses a **two-phase approach**:
1. **Hard Filters** - Binary pass/fail criteria that exclude jobs entirely
2. **Weighted Scoring** - Multi-factor scoring for jobs that pass filters

Only jobs scoring **60+** (configurable) are saved as matches.

---

## Hard Filters

These are checked BEFORE scoring. If any fail, the job is skipped entirely (no match created).

### 1. User Feedback Loop (NEW)

Previously rejected or hidden jobs are never shown again.

| Existing Match Status | Result |
|----------------------|--------|
| `rejected` | EXCLUDED |
| `hidden` | EXCLUDED |
| `matched`, `interested`, `applied` | Continue to other filters |
| No existing match | Continue to other filters |

**How it works**: Before any scoring, the system checks if the user has previously rejected or hidden this job. If so, it's skipped entirely - no LLM calls, no scoring.

### 2. Remote Type Filter

| User Preference | Job Property | Result |
|-----------------|--------------|--------|
| `preferences.remote_types` (list) | `job.remote_type` | Job must be in user's list |
| No preference set | Any | PASS |

**Example**: User wants `["full", "hybrid"]` → Job with `"onsite"` is EXCLUDED

### 3. Employment Eligibility Filter

Two sub-checks:

#### a) Regional Eligibility
| User Preference | Job Property | Result |
|-----------------|--------------|--------|
| `preferences.eligible_regions` | `job.eligible_regions` | At least one region must overlap |
| Either has "Worldwide" | Any | PASS |

**Example**: User eligible in `["EU", "UK"]` → Job requiring `["US only"]` is EXCLUDED

#### b) Visa Sponsorship
| User Needs Visa | Job Offers Visa | Result |
|-----------------|-----------------|--------|
| `true` | `0` (explicit no) | EXCLUDED |
| `true` | `1` (yes) | PASS |
| `true` | `null` (unknown) | PASS (assume possible) |
| `false` | Any | PASS |

### 4. Minimum Skills Extracted (NEW)

Jobs with no extracted skills are skipped entirely.

| LLM Extraction Result | Result |
|----------------------|--------|
| `required_skills = []` AND `nice_to_have_skills = []` | EXCLUDED |
| At least 1 skill extracted | Continue to other filters |

**Why**: If the LLM couldn't extract any skills, the job description is likely too vague or the extraction failed. These jobs would get inflated scores from other factors (title, location, salary) despite having no skill relevance.

### 5. Minimum Skill Overlap (NEW)

User must have at least 1 matching or related skill.

| Skill Match Result | Result |
|-------------------|--------|
| 0 exact matches AND 0 related matches | EXCLUDED |
| At least 1 exact or related match | Continue to scoring |

**Why**: A job with zero skill overlap is not a real match, even if title/salary/location look good. This prevents irrelevant jobs from appearing just because they're senior roles with good pay.

### 6. Seniority Filter

Optionally filter jobs by seniority level (Junior/Mid/Senior).

| User Preference | Job Seniority | Result |
|-----------------|---------------|--------|
| `preferences.seniority_filter = "senior"` | "senior" | PASS |
| `preferences.seniority_filter = "senior"` | "junior" or "mid" | EXCLUDED |
| `preferences.seniority_filter = null` | Any | PASS (no filter) |

**Seniority Detection**:
- **Junior**: Title contains "junior", "jr", "entry", "associate", "graduate", "intern", "trainee" OR experience_min <= 2
- **Senior**: Title contains "senior", "sr", "lead", "principal", "staff", "head", "director", "vp", "chief" OR experience_min >= 5
- **Mid**: Everything else

---

## Weighted Scoring Factors

Jobs that pass hard filters are scored on a 0-100 scale using these weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Skills** | 35% | How well user skills match job requirements (with semantic matching) |
| **Title** | 20% | Role/category alignment with user's background |
| **Experience** | 15% | Years of experience vs job requirements |
| **Location** | 10% | Geographic preference match |
| **Salary** | 10% | Salary expectations vs job offering |
| **Freshness** | 10% | How recently the job was posted (NEW) |

### 1. Skill Match (35%)

**Inputs**:
- `user.skills` (from profile)
- `job_requirements.required_skills` (extracted by LLM)
- `job_requirements.nice_to_have_skills` (extracted by LLM)

**Semantic Skill Matching (NEW)**:
Skills are matched using **skill clusters** for partial credit:
- **Exact match** = 100% credit
- **Related skill** (same cluster) = 50% credit
- **No match** = 0% credit

**Skill Clusters**:
```
python_web: Python, Django, Flask, FastAPI, SQLAlchemy, Celery
javascript_frontend: JavaScript, TypeScript, React, Vue, Angular, Next.js, Svelte
javascript_backend: JavaScript, TypeScript, Node.js, Express, NestJS, Fastify
databases_sql: PostgreSQL, MySQL, SQL Server, SQL, SQLite, MariaDB
databases_nosql: MongoDB, Redis, Elasticsearch, DynamoDB, Cassandra
cloud_aws: AWS, EC2, S3, Lambda, CloudFormation, ECS, EKS, RDS
devops_containers: Docker, Kubernetes, ECS, EKS, GKE, AKS, Podman
ml_frameworks: TensorFlow, PyTorch, scikit-learn, Keras, JAX
```

See `backend/app/utils/skill_clusters.py` for full cluster definitions.

**Example**: User has `Flask` → Job requires `Django` → 50% credit (both in python_web cluster)

**Scoring**:
```
If job has required_skills:
  required_score = (semantic_score / total_required) * 80
  nice_to_have_score = (semantic_score / total_nice_to_have) * 20
  score = required_score + nice_to_have_score

If job has only nice_to_have:
  score = (semantic_score / total) * 100

If job has no skill requirements:
  score = 50 (neutral)
```

**Skill Normalization**:
Skills are normalized to canonical names before comparison:
- `js`, `JS` → `JavaScript`
- `ts`, `typescript` → `TypeScript`
- `reactjs`, `react.js` → `React`
- `postgres`, `pg` → `PostgreSQL`
- `k8s` → `Kubernetes`
- `aws`, `amazon web services` → `AWS`
- See `backend/app/utils/skill_aliases.py` for full mapping

**Returns**: matching_skills, missing_skills, related_skills (NEW)

### 2. Title Match (20%)

**Inputs**:
- `user.preferences.target_roles` OR recent job titles from parsed CV
- `job.title`

**Scoring Categories**:

| Match Type | Score |
|------------|-------|
| Same category (Engineer↔Engineer, Designer↔Designer) | 90 |
| 2+ keyword overlap | 70 |
| 1 keyword overlap | 50 |
| No overlap | 20 |
| IC ↔ Pure Management mismatch | 10 |
| Manager ↔ Pure IC mismatch | 30 |

**Seniority Adjustments**:
- Senior ↔ Senior: +10 bonus (max 100)
- Senior ↔ Non-Senior: -10 penalty

### 3. Experience Match (15%)

**Inputs**:
- `user.experience_years`
- `job_requirements.experience_years_min`
- `job_requirements.experience_years_max`

**Scoring**:

| Situation | Score |
|-----------|-------|
| In range [min, max] | 100 |
| Overqualified (> max) | 90 |
| Under by 1 year | 80 |
| Under by 2 years | 60 |
| Under by 3+ years | 40 |
| No experience data | 50 |

### 4. Location Match (10%)

**Inputs**:
- `user.preferences.preferred_countries`
- `job.location`
- `job.remote_type`

**Scoring**:

| Situation | Score |
|-----------|-------|
| No preference | 100 |
| "Remote" in prefs + job is full remote | 100 |
| Job location contains preferred country | 100 |
| No match | 30 |

### 5. Salary Match (10%)

**Inputs**:
- `user.preferences.min_salary`
- `job.salary_max` (preferred) or `job.salary_min`

**Scoring**:

| Situation | Score |
|-----------|-------|
| No user preference | 100 |
| No job salary info | 50 |
| Job salary >= user minimum | 100 |
| Job salary 90-100% of minimum | 80 |
| Job salary 80-90% of minimum | 60 |
| Job salary < 80% of minimum | 30 |

### 6. Freshness Score (10%) - NEW

**Inputs**:
- `job.posted_at` (preferred)
- Falls back to `job.scraped_at` or `job.created_at`

**Scoring** (gentle decay curve):

| Job Age | Score |
|---------|-------|
| 0-7 days | 100 |
| 7-14 days | 95 |
| 14-30 days | 85 |
| 30+ days | 70 |
| Unknown date | 85 |

**Why**: Encourages applying to recent jobs while not harshly penalizing older postings that might still be relevant.

---

## Final Score Calculation

```
overall_score = (
    skill_score      * 0.35 +
    title_score      * 0.20 +
    experience_score * 0.15 +
    location_score   * 0.10 +
    salary_score     * 0.10 +
    freshness_score  * 0.10
)
```

If `overall_score >= 60` → Match is created/updated
If `overall_score < 60` → No match saved

---

## LLM Usage

### Job Requirements Extraction (Haiku)

Before scoring, the LLM extracts structured data from job descriptions:

```json
{
  "required_skills": ["Python", "Django"],
  "nice_to_have_skills": ["Go", "Kubernetes"],
  "experience_years_min": 3,
  "experience_years_max": 7,
  "education": "Bachelor's in CS",
  "languages": ["English"],
  "job_type": "permanent",
  "remote_type": "full",
  "eligible_regions": ["EU", "Worldwide"],
  "visa_sponsorship": true
}
```

**Caching**: 7-day TTL, keyed by job content hash (shared across users)

---

## Data Flow

```
User + Job
    │
    ├─→ [HARD FILTER] Feedback Loop (rejected/hidden)
    │   ✗ → Skip job (user already rejected)
    │
    ├─→ [HARD FILTER] Remote Type
    │   ✗ → Skip job
    │
    ├─→ [HARD FILTER] Eligibility (region + visa)
    │   ✗ → Skip job
    │
    ├─→ [LLM] Extract job requirements
    │   ✗ → Skip job (extraction failed)
    │
    ├─→ [HARD FILTER] Minimum Skills Extracted
    │   ✗ → Skip job (no skills in job description)
    │
    ├─→ [HARD FILTER] Seniority (if user set preference)
    │   ✗ → Skip job
    │
    ├─→ [SCORE] Calculate all 6 factors
    │
    ├─→ [HARD FILTER] Minimum Skill Overlap
    │   ✗ → Skip job (zero skill match)
    │
    ├─→ [AGGREGATE] Weighted sum
    │
    ├─→ [THRESHOLD] Score >= 60?
    │   ✗ → Skip job
    │
    └─→ [SAVE] Create/update Match record
```

---

## Match Record Structure

```json
{
  "id": 123,
  "user_id": 1,
  "job_id": 456,
  "score": 78.5,
  "status": "matched",
  "reasoning": {
    "overall_score": 78.5,
    "skill_score": 85.0,
    "title_score": 90.0,
    "location_score": 100.0,
    "salary_score": 60.0,
    "experience_score": 85.0,
    "freshness_score": 100.0,
    "matching_skills": ["Python", "Django", "PostgreSQL"],
    "missing_skills": ["Go"],
    "related_skills": ["Flask"],
    "weights": {
      "skills": 0.35,
      "title": 0.20,
      "location": 0.10,
      "salary": 0.10,
      "experience": 0.15,
      "freshness": 0.10
    }
  },
  "analysis": "Strong match based on skills...",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/services/matching.py` | Core matching logic |
| `backend/app/services/llm.py` | LLM extraction functions |
| `backend/app/utils/skill_aliases.py` | Skill normalization & aliases |
| `backend/app/utils/skill_clusters.py` | Semantic skill clustering (NEW) |
| `backend/app/models/match.py` | Match database model |
| `backend/app/routers/matches.py` | API endpoints |
