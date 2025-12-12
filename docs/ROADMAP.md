# Career Agent - Roadmap & Architecture

## Vision

An AI-powered job hunting assistant that:
1. Scrapes job boards for relevant postings
2. Matches jobs against your CV and preferences
3. Generates tailored cover letters and CV highlights
4. Tracks applications and provides insights

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
│                    Python FastAPI (Fly.io)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Jobs API   │  │  Match API  │  │ Generate API│                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
         │                   │                    │
         ▼                   ▼                    ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  PostgreSQL │    │   Redis Cache   │    │ Anthropic   │
│   (Neon)    │    │   (Upstash)     │    │ Claude API  │
└─────────────┘    └─────────────────┘    └─────────────┘
         ▲
         │
┌─────────────────────────────────────────────────────────────────────┐
│                         SCRAPING WORKER                              │
│              Python + Playwright (Fly.io separate app)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  RemoteOK   │  │ WeWorkRemote│  │  LinkedIn   │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | React + TypeScript + Vite | Your strength, fast dev |
| Backend | Python FastAPI | LLM ecosystem, async, learning goal |
| Database | PostgreSQL (Neon) | Free tier, serverless, scales |
| Cache | Redis (Upstash) | Free tier, serverless |
| LLM | Anthropic Claude API | MCP experience, quality |
| Scraping | Playwright | Handles JS-rendered pages |
| IaC | Terraform | Your experience, portable |
| Frontend Hosting | Vercel | Free, easy |
| Backend Hosting | Fly.io | Good free tier, scales |

---

## Data Models

### User
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### CV/Profile
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  raw_cv_text TEXT,
  parsed_cv JSONB,  -- structured extraction
  skills TEXT[],
  experience_years INTEGER,
  preferences JSONB,  -- salary, location, remote, contract type
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Job Posting
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source VARCHAR(50) NOT NULL,  -- remoteok, weworkremotely, linkedin
  source_id VARCHAR(255),  -- original ID from source
  url VARCHAR(500) NOT NULL,
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255),
  description TEXT,
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10),
  location VARCHAR(255),
  remote_type VARCHAR(50),  -- full, hybrid, onsite
  job_type VARCHAR(50),  -- permanent, contract, freelance
  contract_duration VARCHAR(100),  -- 6 months, ongoing, etc.
  requirements JSONB,  -- extracted skills, experience
  raw_data JSONB,  -- original scraped data
  scraped_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  UNIQUE(source, source_id)
);
```

### Job Match
```sql
CREATE TABLE matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  match_score DECIMAL(5,2),  -- 0-100
  skill_matches TEXT[],
  skill_gaps TEXT[],
  analysis JSONB,  -- detailed LLM analysis
  status VARCHAR(50) DEFAULT 'new',  -- new, interested, applied, rejected, hidden
  cover_letter TEXT,
  cv_highlights TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, job_id)
);
```

### Scrape Log
```sql
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
```

---

## API Endpoints

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Login (simple JWT for MVP)

### Profile
- `GET /profile` - Get user profile
- `PUT /profile` - Update profile
- `POST /profile/cv` - Upload and parse CV

### Jobs
- `GET /jobs` - List jobs (with filters)
- `GET /jobs/:id` - Get job details
- `POST /jobs/refresh` - Trigger scrape (admin/manual)

### Matches
- `GET /matches` - Get matched jobs for user
- `POST /matches/:job_id/generate` - Generate cover letter
- `PUT /matches/:job_id/status` - Update status (interested, applied, etc.)

### Admin
- `GET /admin/scrape-logs` - View scrape history
- `POST /admin/scrape` - Trigger manual scrape

---

## Phase 1: Foundation (Week 1-2)

### Goals
- [x] Project scaffolding
- [ ] Database schema + migrations
- [ ] Basic FastAPI setup with health check
- [ ] RemoteOK scraper (they have JSON API)
- [ ] Job storage and deduplication
- [ ] Basic React UI to view jobs

### Deliverables
- Can scrape RemoteOK and store jobs
- Can view jobs in UI with basic filters
- Deployed to Fly.io + Vercel

### Tasks
1. Set up local dev environment (Docker Compose)
2. Create database migrations (Alembic)
3. Build RemoteOK scraper
4. Build jobs API endpoints
5. Build basic React UI
6. Deploy with Terraform

---

## Phase 2: Matching (Week 3-4)

### Goals
- [ ] CV upload and parsing
- [ ] LLM-based requirement extraction from jobs
- [ ] Match scoring algorithm
- [ ] Skill gap analysis
- [ ] Ranked job list UI

### Deliverables
- Upload CV, get matched jobs with scores
- See skill gaps per job
- Filter by match score

### Tasks
1. CV upload endpoint + storage
2. LLM prompt for CV parsing
3. LLM prompt for job requirement extraction
4. Matching algorithm (LLM or embeddings)
5. Match results UI
6. Caching layer for LLM results

---

## Phase 3: Generation (Week 5-6)

### Goals
- [ ] Cover letter generation
- [ ] CV highlights/tailoring
- [ ] Application tracking
- [ ] Email notifications (optional)

### Deliverables
- Generate tailored cover letter per job
- Track application status
- Export cover letter as text/PDF

### Tasks
1. Cover letter generation prompt
2. CV highlights prompt
3. Generation UI with editing
4. Status tracking UI
5. PDF export

---

## Phase 4: Polish & Scale (Week 7-8)

### Goals
- [ ] Add more job sources (WeWorkRemotely, LinkedIn)
- [ ] Scheduled scraping (cron)
- [ ] Better UI/UX
- [ ] Performance optimization
- [ ] Write case study for portfolio

### Deliverables
- Production-ready app
- Portfolio case study
- (Optional) Public launch

---

## Cost Estimate (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Neon (Postgres) | Free | $0 |
| Upstash (Redis) | Free | $0 |
| Fly.io (Backend) | Free allowance | $0-5 |
| Fly.io (Scraper) | Free allowance | $0-5 |
| Vercel (Frontend) | Free | $0 |
| Anthropic API | Pay as you go | $10-20 |
| **Total** | | **$10-30** |

---

## Infrastructure (Terraform)

### Providers
- Neon (PostgreSQL) - has Terraform provider
- Upstash (Redis) - has Terraform provider
- Fly.io - has Terraform provider
- Vercel - has Terraform provider

### Structure
```
infrastructure/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── modules/
│   │   ├── database/
│   │   ├── cache/
│   │   ├── backend/
│   │   └── frontend/
│   └── environments/
│       ├── dev.tfvars
│       └── prod.tfvars
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Auth
JWT_SECRET=...

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Getting Started (for Claude Code)

```bash
# 1. Clone repo
git clone https://github.com/denisenanni/career-agent.git
cd career-agent

# 2. Install frontend dependencies
yarn install

# 3. Set up backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Start local services
docker-compose up -d

# 5. Run migrations
cd backend
alembic upgrade head

# 6. Start dev servers
yarn dev
```

---

## Notes

- Start with Haiku for extraction, Sonnet for generation
- Cache LLM results aggressively (same job = same extraction)
- RemoteOK has a JSON API at https://remoteok.com/api
- LinkedIn scraping is harder - save for Phase 4
- Keep it simple first, optimize later
