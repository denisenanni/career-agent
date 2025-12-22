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

### 1. Remote Type Filter

| User Preference | Job Property | Result |
|-----------------|--------------|--------|
| `preferences.remote_types` (list) | `job.remote_type` | Job must be in user's list |
| No preference set | Any | PASS |

**Example**: User wants `["full", "hybrid"]` → Job with `"onsite"` is EXCLUDED

### 2. Employment Eligibility Filter

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

---

## Weighted Scoring Factors

Jobs that pass hard filters are scored on a 0-100 scale using these weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Skills** | 40% | How well user skills match job requirements |
| **Title** | 20% | Role/category alignment with user's background |
| **Experience** | 20% | Years of experience vs job requirements |
| **Location** | 10% | Geographic preference match |
| **Salary** | 10% | Salary expectations vs job offering |

### 1. Skill Match (40%)

**Inputs**:
- `user.skills` (from profile)
- `job_requirements.required_skills` (extracted by LLM)
- `job_requirements.nice_to_have_skills` (extracted by LLM)

**Scoring**:
```
If job has required_skills:
  required_score = (matched_required / total_required) * 80
  nice_to_have_score = (matched_nice_to_have / total_nice_to_have) * 20
  score = required_score + nice_to_have_score

If job has only nice_to_have:
  score = (matched / total) * 100

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

**Notes**:
- Case-insensitive matching with alias resolution
- Required skills worth 4x more than nice-to-have
- Returns: matching_skills list, missing_skills list

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

### 3. Experience Match (20%)

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

---

## Final Score Calculation

```
overall_score = (
    skill_score     * 0.40 +
    title_score     * 0.20 +
    experience_score * 0.20 +
    location_score  * 0.10 +
    salary_score    * 0.10
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
    ├─→ [HARD FILTER] Remote Type
    │   ✗ → Skip job
    │
    ├─→ [HARD FILTER] Eligibility (region + visa)
    │   ✗ → Skip job
    │
    ├─→ [LLM] Extract job requirements
    │   ✗ → Skip job (extraction failed)
    │
    ├─→ [SCORE] Calculate all 5 factors
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
    "matching_skills": ["Python", "Django", "PostgreSQL"],
    "missing_skills": ["Go", "Rust"],
    "weights": {
      "skills": 0.40,
      "title": 0.20,
      "location": 0.10,
      "salary": 0.10,
      "experience": 0.20
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
| `backend/app/models/match.py` | Match database model |
| `backend/app/routers/matches.py` | API endpoints |
