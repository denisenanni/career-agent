# Career Agent - Project Plan

## Overview

An AI-powered job hunting assistant that:
1. Scrapes job boards for relevant postings
2. Matches jobs against your CV and preferences
3. Generates tailored cover letters and CV highlights
4. Tracks applications and provides insights

**Repository:** https://github.com/denisenanni/career-agent

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                    React + TypeScript + Vite                        │
│                         (Vercel)                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                    │
│                    Python FastAPI (Railway)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Jobs API   │  │  Match API  │  │ Generate API│                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
         │                   │                    │
         ▼                   ▼                    ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  PostgreSQL │    │   Redis Cache   │    │ Anthropic   │
│  (Railway)  │    │   (Railway)     │    │ Claude API  │
└─────────────┘    └─────────────────┘    └─────────────┘
         ▲
         │
┌─────────────────────────────────────────────────────────────────────┐
│                         SCRAPING WORKER                              │
│                    Python + httpx (same backend)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  RemoteOK   │  │ WeWorkRemote│  │  LinkedIn   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React + TypeScript + Vite + Tailwind | Already scaffolded |
| Backend | Python FastAPI | Already scaffolded |
| Database | PostgreSQL (Railway) | All-in-one platform |
| Cache | Redis (Railway) | All-in-one platform |
| LLM | Anthropic Claude API | Haiku for extraction, Sonnet for generation |
| Scraping | httpx + Playwright | Start with httpx for APIs |
| Infrastructure | Terraform | Railway + Vercel providers |
| Frontend Hosting | Vercel | Free tier |
| Backend Hosting | Railway | $5/month credit |

---

## Infrastructure (Terraform)

### Providers

```hcl
terraform {
  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "~> 0.4"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 1.0"
    }
  }
}
```

### Railway resources

1. **Project** - `career-agent-dev`
2. **PostgreSQL service** - Database
3. **Redis service** - Cache
4. **Backend service** - FastAPI app (connected to GitHub repo)

### Vercel resources

1. **Project** - Frontend (connected to GitHub repo, root: `/frontend`)

### Environment variables

**Railway Backend Service:**
- `DATABASE_URL` - Auto-injected from Railway Postgres
- `REDIS_URL` - Auto-injected from Railway Redis
- `ANTHROPIC_API_KEY` - From Anthropic console
- `JWT_SECRET` - Generate with `openssl rand -base64 32`
- `ENVIRONMENT` - `production`

**Vercel Frontend:**
- `VITE_API_URL` - Railway backend URL

---

## Database Schema

```sql
-- Users (simple for MVP)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Profiles
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  raw_cv_text TEXT,
  parsed_cv JSONB,
  skills TEXT[],
  experience_years INTEGER,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Jobs
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source VARCHAR(50) NOT NULL,
  source_id VARCHAR(255) NOT NULL,
  url VARCHAR(500) NOT NULL,
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255),
  description TEXT,
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10) DEFAULT 'USD',
  location VARCHAR(255),
  remote_type VARCHAR(50),
  job_type VARCHAR(50),
  contract_duration VARCHAR(100),
  requirements JSONB,
  tags TEXT[],
  raw_data JSONB,
  scraped_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  UNIQUE(source, source_id)
);

-- Matches
CREATE TABLE matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  match_score DECIMAL(5,2),
  skill_matches TEXT[],
  skill_gaps TEXT[],
  analysis JSONB,
  status VARCHAR(50) DEFAULT 'new',
  cover_letter TEXT,
  cv_highlights TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, job_id)
);

-- Scrape logs
CREATE TABLE scrape_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source VARCHAR(50) NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  jobs_found INTEGER DEFAULT 0,
  jobs_new INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'running',
  error TEXT
);

CREATE TABLE skill_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  analysis_date TIMESTAMP DEFAULT NOW(),
  market_skills JSONB,
  user_skills JSONB,
  skill_gaps JSONB,
  recommendations JSONB,
  jobs_analyzed INTEGER,
  UNIQUE(user_id)
)

-- Indexes
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at DESC);
CREATE INDEX idx_matches_user_id ON matches(user_id);
CREATE INDEX idx_matches_score ON matches(match_score DESC);
```

---

## API Endpoints

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Login (JWT)
- `POST /auth/logout` - Logout

### Profile
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update profile
- `POST /api/profile/cv` - Upload and parse CV

### Jobs
- `GET /api/jobs` - List jobs (with filters)
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/refresh` - Trigger scrape

### Matches
- `GET /api/matches` - Get matched jobs for user
- `POST /api/matches/{job_id}/generate` - Generate cover letter
- `PUT /api/matches/{job_id}/status` - Update status

---

## Phases

### Phase 1: Infrastructure & Local Dev (Days 1-2)

**Tasks:**
1. Update Terraform config for Railway (remove Fly.io, Neon, Upstash)
2. Update docker-compose.yml to Postgres 17
3. Set up Alembic migrations
4. Create all database tables
5. Verify backend runs locally (`curl http://localhost:8000/health`)
6. Verify frontend runs locally (http://localhost:5173)

**Deliverables:**
- [x] Terraform config for Railway + Vercel
- [x] Local dev working (docker-compose + backend + frontend)
- [x] Database migrations running

---

### Phase 2: Job Scraping (Days 3-5)

**Tasks:**
1. Connect RemoteOK scraper to database
2. Add deduplication (upsert by source + source_id)
3. Add scrape logging
4. Implement Jobs API endpoints
5. Build Jobs UI (list, filters, detail view)
6. (Stretch) Add WeWorkRemotely scraper

**Deliverables:**
- [x] RemoteOK scraper storing to database
- [x] Jobs API working
- [x] Jobs UI with filters

---

### Phase 3: Profile & CV Parsing (Days 6-8)

**Tasks:**
1. ✅ Auth endpoints (register, login, JWT)
2. ✅ CV upload endpoint (PDF, DOCX, TXT)
3. ✅ Text extraction (pypdf, python-docx)
4. ✅ LLM parsing with Claude Haiku
5. ✅ Preferences storage
6. Profile UI (upload, parsed view, preferences form)

**LLM Prompt - CV Parsing:**
```
Extract structured information from this CV. Return JSON only.

{
  "name": "string",
  "email": "string or null",
  "phone": "string or null",
  "summary": "brief professional summary",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "YYYY-MM or null",
      "end_date": "YYYY-MM or null or 'present'",
      "description": "brief description"
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string or null",
      "end_date": "YYYY or null"
    }
  ],
  "years_of_experience": number
}

CV Text:
---
{cv_text}
```

**Implementation Details:**
- Backend service: `app/services/llm.py` - Claude Haiku integration
- CV parsing: `app/routers/profile.py` - Auto-parsing on upload
- Endpoints:
  - ✅ `POST /auth/register` - User registration with bcrypt
  - ✅ `POST /auth/login` - JWT token (7-day expiration)
  - ✅ `POST /auth/logout` - Logout endpoint
  - ✅ `GET /auth/me` - Get current user
  - ✅ `GET /api/profile` - Get profile (includes parsed_cv in preferences)
  - ✅ `PUT /api/profile` - Update profile
  - ✅ `POST /api/profile/cv` - Upload CV (extracts text + parses with Haiku)
  - ✅ `GET /api/profile/cv/parsed` - Get parsed CV data

**Deliverables:**
- [x] Register/login/logout
- [x] CV upload working
- [x] LLM parsing working
- [x] Profile UI complete

---

### Phase 4: Job Matching & Career Insights (Days 9-14)

**Tasks:**
1. Job requirement extraction with Claude Haiku
2. Cache extraction results (same job = same extraction)
3. Matching algorithm (skills comparison, score 0-100)
4. Skill gap analysis per job
5. **Market analysis** - aggregate skills across all scraped jobs
6. **Career recommendations** - suggest skills to develop based on:
   - Frequency in job postings
   - Salary impact
   - Learning effort given existing skills
7. Matches API
8. **Insights API** - `/api/insights/skills` endpoint
9. Matches UI (ranked list, skill visualization)
10. **Insights UI** - show recommended skills to develop


**LLM Prompt - Job Extraction:**
```
Extract job requirements from this posting. Return JSON only.

{
  "required_skills": ["skill1", "skill2", ...],
  "nice_to_have_skills": ["skill1", "skill2", ...],
  "experience_years_min": number or null,
  "experience_years_max": number or null,
  "education": "string or null",
  "languages": ["English", ...],
  "job_type": "permanent" | "contract" | "freelance" | "part-time",
  "remote_type": "full" | "hybrid" | "onsite",
  "salary_min": number or null,
  "salary_max": number or null,
  "salary_currency": "USD" | "EUR" | etc
}

Job Posting:
---
Title: {title}
Company: {company}
Description: {description}
```

**Deliverables:**
- [ ] Job extraction with caching
- [ ] Matching algorithm
- [ ] Matches API
- [ ] Matches UI
- [ ] Market skill analysis
- [ ] Career recommendations
- [ ] Insights UI

---

### Phase 5: Application Generation (Days 13-16)

**Tasks:**
1. Cover letter generation with Claude Sonnet
2. CV highlights generation
3. Generation API endpoint
4. Generation UI (generate, edit, copy)
5. (Optional) PDF export

**LLM Prompt - Cover Letter:**
```
Write a cover letter for this job application. Be professional but personable.
Highlight relevant experience. Keep it under 400 words.

Candidate Profile:
- Name: {name}
- Skills: {skills}
- Experience: {experience_summary}

Job Details:
- Title: {title}
- Company: {company}
- Requirements: {requirements}

Match Analysis:
- Matching skills: {skill_matches}
- Gaps to address: {skill_gaps}

Write the cover letter:
```

**Deliverables:**
- [ ] Cover letter generation
- [ ] CV highlights
- [ ] Generation UI

---

### Phase 6: Deploy & Polish (Days 17-20)

**Tasks:**
1. Run `terraform apply`
2. Verify Railway deployment
3. Verify Vercel deployment
4. Set up GitHub Actions CI
5. Add scheduled scraping (Railway cron)
6. Polish UI (loading, errors, mobile)
7. Write portfolio case study

**Deliverables:**
- [ ] Production deployment
- [ ] CI/CD pipeline
- [ ] Scheduled scraping
- [ ] Portfolio write-up

---

### Phase 7: Performance Optimizations (Future)

**Critical Optimizations (COMPLETED):**
- [x] LLM response caching (SHA256 hash-based)
- [x] React Query for API caching (5-minute stale time)
- [x] Rate limiting on CV upload (5/hour per IP)
- [x] Full-text search index for jobs (PostgreSQL tsvector + GIN index)
- [x] React component memoization (JobCard, AuthContext)

**Medium Priority Optimizations:**
- [ ] Optimize count query in jobs endpoint (use window function)
- [ ] Add code splitting for React routes
- [ ] Add LLM timeout handling (30s timeout)
- [ ] Add composite indexes for match queries

**Low Priority Optimizations:**
- [ ] Stream file uploads for large CVs
- [ ] Optimize JWT to reduce DB lookups
- [ ] Batch job analysis with LLM
- [ ] Add Redis for distributed caching (production)

**Performance Improvements Expected:**
- LLM Caching: 90% faster on cache hits (2-5s → 50ms)
- React Query: 80% faster page transitions
- Full-text search: 95% faster search queries (100ms → 5ms)
- Memoization: 30% fewer React re-renders
- Rate limiting: Cost protection and abuse prevention

**Files Modified:**
- `backend/app/services/llm.py` - Added in-memory cache with LRU eviction
- `backend/app/main.py` - Added slowapi rate limiter
- `backend/app/routers/profile.py` - Added rate limiting to CV upload
- `backend/migrations/versions/b9152b597093_add_fulltext_search_index.py` - Added tsvector + GIN index
- `backend/app/routers/jobs.py` - Updated search to use full-text search
- `frontend/src/pages/JobsPage.tsx` - Refactored with React Query + useMemo
- `frontend/src/components/JobCard.tsx` - Added memo + useMemo
- `frontend/src/contexts/AuthContext.tsx` - Added useCallback + useMemo
- `backend/requirements.txt` - Added slowapi==0.1.9

---

## File Structure

```
career-agent/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── JobCard.tsx
│   │   │   ├── MatchCard.tsx
│   │   │   ├── CVUpload.tsx
│   │   │   └── Filters.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── JobsPage.tsx
│   │   │   ├── MatchesPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── hooks/
│   │   │   ├── useJobs.ts
│   │   │   ├── useMatches.ts
│   │   │   └── useProfile.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── types/
│   │       └── index.ts
│   └── ...
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── llm/
│   ├── alembic/
│   └── requirements.txt
├── scraping/
│   └── scrapers/
│       ├── remoteok.py
│       └── weworkremotely.py
├── infrastructure/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── providers.tf
├── docker-compose.yml
├── package.json
└── README.md
```

---

## API Keys Needed

| Service | URL |
|---------|-----|
| Anthropic | https://console.anthropic.com/ |
| Railway | https://railway.app/account/tokens |
| Vercel | https://vercel.com/account/tokens |

---

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| Railway (Backend + Postgres + Redis) | $0-5 |
| Vercel (Frontend) | $0 |
| Anthropic API | $10-20 |
| **Total** | **$10-25** |

---

## Commands Reference

```bash
# Local development
docker-compose up -d          # Start Postgres + Redis
yarn install                  # Install frontend deps
yarn backend:setup            # Set up Python venv
yarn dev                      # Start frontend + backend

# Database
yarn db:migrate               # Run migrations

# Terraform
cd infrastructure/terraform
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars

# Testing scraper
cd scraping
python -m scrapers.remoteok
```

---

## Notes

- Use Haiku for extraction (cheap), Sonnet for generation (quality)
- Cache LLM results aggressively
- RemoteOK has JSON API at https://remoteok.com/api
- LinkedIn scraping is harder - save for later
- Test locally before deploying
- Commit frequently