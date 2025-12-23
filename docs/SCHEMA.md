# Database Schema

This document describes the complete database schema for the Career Agent application.

## Overview

The database uses **PostgreSQL 17** in production and SQLite for testing. All tables use integer primary keys with automatic timestamps.

---

## Tables

### 1. Users

Stores user authentication credentials and profile information.

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,

  -- Authentication
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,

  -- Profile
  full_name VARCHAR(255),
  bio TEXT,
  skills JSONB DEFAULT '[]',           -- List of user's skills
  experience_years INTEGER,

  -- Preferences
  preferences JSONB DEFAULT '{}',      -- Job preferences + parsed CV data

  -- CV
  cv_text TEXT,                        -- Extracted text from uploaded CV
  cv_filename VARCHAR(255),
  cv_uploaded_at TIMESTAMP,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
```

**Notes:**
- `skills` array stores user's current technical skills
- `preferences` JSON stores job filters, target_roles, parsed CV data, etc.
- Password is hashed using bcrypt before storage
- `cv_text` contains the raw extracted text from PDF/DOCX/TXT uploads

---

### 2. Jobs

Stores scraped job postings from various sources.

```sql
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,

  -- Source tracking
  source VARCHAR(50) NOT NULL,         -- remoteok, weworkremotely, etc.
  source_id VARCHAR(255) NOT NULL,     -- External job ID from source
  url VARCHAR(500) NOT NULL,

  -- Job details
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,

  -- Compensation
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10) DEFAULT 'USD',

  -- Location
  location VARCHAR(255) DEFAULT 'Remote',
  remote_type VARCHAR(50) DEFAULT 'full',  -- full, partial, none
  job_type VARCHAR(50) DEFAULT 'permanent', -- permanent, contract, part-time

  -- Skills/tags
  tags JSONB DEFAULT '[]',
  raw_data JSONB,                      -- Original JSON from scraper

  -- Timestamps
  posted_at TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT NOW() NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

  -- Full-text search
  search_vector TSVECTOR,              -- Auto-updated by trigger (PostgreSQL only)

  -- Constraints
  CONSTRAINT uq_jobs_source_source_id UNIQUE (source, source_id)
);

-- Indexes
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_source_id ON jobs(source_id);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at DESC);
CREATE INDEX idx_jobs_search_vector ON jobs USING GIN(search_vector);
```

**Notes:**
- Composite unique constraint on `(source, source_id)` prevents duplicate jobs
- `search_vector` is populated by database trigger for full-text search
- `tags` array contains job-specific skills/technologies
- `raw_data` preserves original scraper response for debugging

---

### 3. Matches

Stores job matches for users with AI-generated analysis and application materials.

```sql
CREATE TABLE matches (
  id SERIAL PRIMARY KEY,

  -- Relationships
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE NOT NULL,

  -- Match scoring
  score DECIMAL(5,2) NOT NULL,         -- Overall match score (0-100)
  reasoning JSONB,                     -- Detailed breakdown (skills, experience, etc.)
  analysis TEXT,                       -- AI-generated match explanation

  -- Application tracking
  status VARCHAR(50) DEFAULT 'matched', -- matched, interested, applied, rejected, hidden
  applied_at TIMESTAMP,

  -- Generated content (cached from Claude API)
  cover_letter TEXT,                   -- Generated cover letter
  cv_highlights TEXT,                  -- Tailored CV bullet points

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

  -- Constraints
  UNIQUE(user_id, job_id)
);

-- Indexes
CREATE INDEX idx_matches_user_id ON matches(user_id);
CREATE INDEX idx_matches_job_id ON matches(job_id);
CREATE INDEX idx_matches_score ON matches(score DESC);
CREATE INDEX idx_matches_user_score ON matches(user_id, score DESC);
CREATE INDEX idx_matches_user_status ON matches(user_id, status);
```

**Notes:**
- `reasoning` JSON contains structured score breakdown:
  ```json
  {
    "overall_score": 85.5,
    "skill_score": 90,
    "title_score": 80,
    "experience_score": 85,
    "work_type_score": 100,
    "location_score": 100,
    "salary_score": 75,
    "matching_skills": ["Python", "React"],
    "missing_skills": ["Docker"],
    "weights": {"skills": 0.35, "title": 0.20, ...}
  }
  ```
- `cover_letter` and `cv_highlights` are generated on-demand and cached
- Composite unique constraint prevents duplicate matches for same user-job pair

---

### 4. Scrape Logs

Tracks scraping operations for monitoring and debugging.

```sql
CREATE TABLE scrape_logs (
  id SERIAL PRIMARY KEY,

  source VARCHAR(50) NOT NULL,
  started_at TIMESTAMP DEFAULT NOW() NOT NULL,
  completed_at TIMESTAMP,

  jobs_found INTEGER DEFAULT 0,
  jobs_new INTEGER DEFAULT 0,

  status VARCHAR(50) DEFAULT 'running', -- running, completed, failed
  error TEXT,

  INDEX idx_scrape_logs_source ON scrape_logs(source),
  INDEX idx_scrape_logs_started_at ON scrape_logs(started_at DESC)
);
```

**Notes:**
- Tracks each scraping session
- `jobs_found` = total jobs scraped
- `jobs_new` = new jobs added (not duplicates)
- `error` contains stack trace if scraping fails

---

### 5. Skill Analysis

Stores market analysis and skill recommendations for users.

```sql
CREATE TABLE skill_analysis (
  id SERIAL PRIMARY KEY,

  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL UNIQUE,

  -- Analysis metadata
  analysis_date TIMESTAMP DEFAULT NOW() NOT NULL,
  jobs_analyzed INTEGER,

  -- Market data (aggregated from all jobs)
  market_skills JSONB DEFAULT '{}',

  -- User data
  user_skills JSONB DEFAULT '[]',
  skill_gaps JSONB DEFAULT '[]',

  -- AI recommendations
  recommendations JSONB DEFAULT '[]'
);

CREATE INDEX idx_skill_analysis_user_id ON skill_analysis(user_id);
```

**Notes:**
- One analysis record per user (enforced by UNIQUE constraint)
- `market_skills` format:
  ```json
  {
    "Python": {
      "count": 150,
      "frequency": 0.75,
      "avg_salary": 120000,
      "jobs_with_salary": 100
    }
  }
  ```
- `recommendations` format:
  ```json
  [
    {
      "skill": "Docker",
      "priority": "high",
      "reason": "Appears in 60% of matching jobs",
      "learning_effort": "low",
      "salary_impact": 15000,
      "frequency": 120
    }
  ]
  ```

---

### 6. Custom Skills

Tracks user-contributed skills that don't appear in job tags.

```sql
CREATE TABLE custom_skills (
  id SERIAL PRIMARY KEY,

  skill VARCHAR(255) UNIQUE NOT NULL,
  usage_count INTEGER DEFAULT 1,       -- Number of users with this skill

  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_custom_skills_skill ON custom_skills(skill);
CREATE INDEX idx_custom_skills_usage_count ON custom_skills(usage_count DESC);
```

**Notes:**
- Allows users to add skills not found in job postings
- `usage_count` incremented when multiple users add the same skill
- Used to populate autocomplete dropdown in Skills UI
- Combined with job tags for comprehensive skill suggestions

---

### 7. User Jobs

Stores user-submitted job postings (jobs users paste/submit manually).

```sql
CREATE TABLE user_jobs (
  id SERIAL PRIMARY KEY,

  -- Relationships
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  job_entry_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,  -- Link to jobs table for matching

  -- Job details
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255),
  description TEXT NOT NULL,
  url VARCHAR(500),
  source VARCHAR(50) DEFAULT 'user_submitted',

  -- Extracted fields (same as scraped jobs)
  tags JSONB DEFAULT '[]',
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10) DEFAULT 'USD',
  location VARCHAR(255),
  remote_type VARCHAR(50),            -- full, hybrid, onsite
  job_type VARCHAR(50),               -- permanent, contract, part-time

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT uq_user_jobs_user_company_title UNIQUE (user_id, company, title)
);

CREATE INDEX idx_user_jobs_user_id ON user_jobs(user_id);
CREATE INDEX idx_user_jobs_job_entry_id ON user_jobs(job_entry_id);
```

**Notes:**
- Allows users to paste job postings from external sources
- `job_entry_id` links to corresponding Job entry for matching system
- When deleted, also deletes the linked Job entry and any matches
- Unique constraint prevents duplicate submissions per user
- Automatically creates a match when job is submitted

---

### 8. Allowed Emails

Stores emails allowed to register (when REGISTRATION_MODE=allowlist).

```sql
CREATE TABLE allowed_emails (
  id SERIAL PRIMARY KEY,

  email VARCHAR(255) UNIQUE NOT NULL,
  added_by INTEGER REFERENCES users(id),

  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_allowed_emails_email ON allowed_emails(email);
```

---

## Database Triggers

### Full-Text Search Trigger (PostgreSQL only)

Automatically updates `search_vector` when jobs are inserted or updated:

```sql
-- Trigger function
CREATE FUNCTION jobs_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.company, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER jobs_search_vector_trigger
BEFORE INSERT OR UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION jobs_search_vector_update();
```

**Purpose:** Enables fast full-text search across job titles, companies, and descriptions with weighted results (titles ranked highest, then companies, then descriptions).

---

## Relationships

```
users (1) ─────< (many) matches (many) ─────> (1) jobs
   │
   └──────────< (1) skill_analysis
```

- Each user can have many matches
- Each job can be matched by many users
- Each user has at most one skill analysis record
- All relationships use CASCADE delete for data consistency

---

## Data Types

### JSON/JSONB Columns

All JSON columns use PostgreSQL's `JSONB` type for efficient indexing and querying. In SQLite tests, these fall back to `TEXT` with JSON serialization.

### Timestamps

All timestamps use `TIMESTAMP WITHOUT TIME ZONE` and store UTC values. Application code converts to user timezone when displaying.

### Custom Types

- **TSVectorType**: Custom SQLAlchemy type that uses `TSVECTOR` in PostgreSQL and `TEXT` in SQLite for test compatibility.

---

## Indexes Summary

| Table | Index Type | Purpose |
|-------|------------|---------|
| users | B-tree on email | Fast user lookup during auth |
| jobs | GIN on search_vector | Full-text search |
| jobs | B-tree on (source, scraped_at) | Efficient pagination |
| matches | B-tree on (user_id, score DESC) | Fast match ranking |
| matches | B-tree on (user_id, status) | Filter by application status |
| skill_analysis | B-tree on user_id | One analysis per user |
| custom_skills | B-tree on skill | Autocomplete queries |

---

## Migration Management

Migrations are managed using **Alembic**:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

All migrations are version-controlled in `backend/migrations/versions/`.

---

## Schema Evolution

### Recent Changes

1. **v2024-12** - Added unique constraint on matches (user_id, job_id) to prevent duplicates
2. **v2024-12** - Added `job_entry_id` column to user_jobs for cascade deletion
3. **v2024-12** - Added `user_jobs` and `allowed_emails` tables
4. **v2024-12** - Added `TSVectorType` custom type for cross-database compatibility
5. **v2024-12** - Added `custom_skills` table for user-contributed skills
6. **v2024-12** - Added `cover_letter` and `cv_highlights` to matches table
7. **v2024-12** - Added composite unique constraint on jobs (source, source_id)
8. **v2024-11** - Added full-text search with GIN index on jobs
9. **v2024-11** - Added composite indexes on matches for performance
