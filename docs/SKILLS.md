# Skills System Architecture

## Overview

The skills system allows users to add skills to their profile, with support for both job-derived skills and custom user-contributed skills.

## Database Models

### 1. User Skills (JSON in User Model)

**Location:** `backend/app/models/user.py`

- Stored as `Column(JSON, default=list)` in the `users` table
- Simple array: `["Python", "React", "Docker"]`
- Direct ownership - no join table

### 2. Custom Skills Table (Global Registry)

**Location:** `backend/app/models/custom_skill.py`

```
custom_skills table:
- id (Primary Key)
- skill (String, UNIQUE, INDEXED)
- usage_count (Integer, default=1)
- created_at, updated_at (DateTime)
```

**Purpose:** Tracks user-contributed skills not found in job tags. Acts as a global discovery pool.

### 3. Skill Analysis Table

**Location:** `backend/app/models/skill_analysis.py`

One-to-one with users for AI-generated skill gap analysis. Contains market_skills, user_skills, skill_gaps, and recommendations.

## Data Flow

### Adding a Skill

1. User types skill in `SkillAutocompleteModal`
2. If custom (not in suggestions): `POST /api/skills/custom` registers it globally
3. Skill added to user's local state
4. `updateParsedCV()` saves to backend
5. Backend updates `user.skills` array

### Removing a Skill

1. User clicks delete in `ParsedCVDisplay`
2. Frontend filters skill from array
3. Backend overwrites `user.skills` with new array
4. **CustomSkill table unchanged** - skill remains for other users

## Skill Search (`GET /api/skills/popular`)

**Location:** `backend/app/routers/skills.py` (lines 39-106)

### Data Sources (merged)

1. **Job Tags** - Extracts all tags from jobs table with frequency count
2. **Custom Skills** - All entries from custom_skills table

### Merge Logic

- Custom skill exists in job_skills: adds usage_count to job frequency
- Otherwise: uses usage_count as frequency
- Result sorted by frequency descending

### Filtering

Removes:
- Blacklisted generic terms (engineer, developer, designer, etc.)
- Single letters
- Skills with length <= 1

Returns top N (default 200, max 500)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/skills/popular` | GET | Get popular skills (jobs + custom) |
| `/api/skills/custom` | POST | Add or increment custom skill |
| `/api/profile` | PUT | Update user profile (includes skills) |
| `/api/profile/cv/parsed` | GET/PUT | Get/update parsed CV (includes skills) |

## Key Design Decisions

1. **Skills as JSON in User model** - Simple, fast, not normalized
2. **Separate custom_skills table** - Enables global discovery
3. **No deletion of custom skills** - Only removed from user profile, not global pool
4. **No usage_count decrement** - Custom skills persist forever
5. **Case-insensitive matching** - "python" matches "Python"

## Known Issues / Gaps

1. **usage_count never decrements** - If user removes skill, global count stays same
2. **No cleanup mechanism** - Orphaned custom skills with usage_count=1 remain forever

## Recent Fixes

### Search Parameter (Dec 2025)

**Problem:** Custom skills with low `usage_count` wouldn't appear in suggestions because the endpoint only returned top 200 skills by frequency.

**Solution:** Added `search` query parameter to `/api/skills/popular`:
- Backend filters skills by name match BEFORE applying the limit
- Frontend performs debounced API search (300ms) when user types
- Merges search results with initial 200 skills for complete suggestions

**Files changed:**
- `backend/app/routers/skills.py` - Added `search` parameter
- `frontend/src/api/skills.ts` - Added `search` param to `getPopularSkills()`
- `frontend/src/components/SkillAutocompleteModal.tsx` - Debounced API search on typing

### Partial Matching in Jobs Search and Filter (Dec 2025)

**Problem:** Both the main search box and skill filter required exact/complete word matches. Searching for "pytho" would find no jobs, but "python" would work.

**Solution:**
1. **Main search**: Changed from `plainto_tsquery` to `to_tsquery` with `:*` prefix operator
   - "pytho" becomes `pytho:*` which matches words starting with "pytho"
   - Multiple words use AND matching (all must match)
   - Input sanitized to prevent tsquery syntax errors

2. **Skill filter**: Changed from exact match to LIKE matching
   - `lower(tag) = :skill` became `lower(tag) LIKE :skill` with `%` wildcards

**Files changed:**
- `backend/app/routers/jobs.py` - Updated both search and skill filter logic

### Insight Skills Saved to Custom Skills (Dec 2025)

**Problem:** Skills recommended by the insights system (e.g., "responsive design" from `SKILL_PATHS`) weren't saved to the `custom_skills` table, so users couldn't find them when searching for skills to add to their profile.

**Solution:** Added `ensure_skills_exist_in_db()` function that saves recommended skills to `custom_skills` table when generating recommendations:
- Skills are saved with `usage_count=0` to indicate they're system-added
- When users actually add the skill, the count increments normally
- This makes insight-recommended skills discoverable in the skill autocomplete

**Files changed:**
- `backend/app/services/insights.py` - Added `ensure_skills_exist_in_db()` function and integrated it into `generate_skill_recommendations()`
