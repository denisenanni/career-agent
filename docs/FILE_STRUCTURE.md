# Project File Structure

This document describes the complete file and directory structure of the Career Agent application.

---

## Overview

The project is organized as a monorepo with separate frontend (React), backend (FastAPI), scraping scripts, infrastructure code, and documentation.

```
career-agent/
├── frontend/          # React + TypeScript + Vite
├── backend/           # Python FastAPI API server
├── scraping/          # Job scraping scripts
├── infrastructure/    # Terraform IaC
├── docs/              # Documentation
├── shared/            # Shared workspace (yarn)
├── docker-compose.yml
├── package.json       # Root package.json (yarn workspaces)
└── README.md
```

---

## Frontend (`/frontend`)

React application built with TypeScript, Vite, and Tailwind CSS.

```
frontend/
├── src/
│   ├── components/              # Reusable UI components
│   │   ├── Layout.tsx          # Main layout wrapper with navigation
│   │   ├── JobCard.tsx         # Job listing card
│   │   ├── MatchCard.tsx       # Match listing with score visualization
│   │   ├── CVUpload.tsx        # File upload component for CVs
│   │   ├── ParsedCVDisplay.tsx # Display parsed CV data with edit
│   │   ├── PreferencesForm.tsx # Job preferences form
│   │   ├── ApplicationMaterialsModal.tsx  # Cover letter + CV highlights UI
│   │   ├── SkillAutocompleteModal.tsx     # Skills autocomplete dropdown
│   │   ├── ProtectedRoute.tsx  # Route guard for authenticated pages
│   │   └── __tests__/          # Component tests (Vitest)
│   │       ├── JobCard.test.tsx
│   │       └── ProtectedRoute.test.tsx
│   ├── pages/                   # Route pages
│   │   ├── HomePage.tsx        # Landing page
│   │   ├── JobsPage.tsx        # Browse all jobs with filters
│   │   ├── MatchesPage.tsx     # User's job matches ranked by score
│   │   ├── ProfilePage.tsx     # User profile + CV upload
│   │   ├── InsightsPage.tsx    # Market insights + skill recommendations
│   │   ├── LoginPage.tsx       # Login form
│   │   └── RegisterPage.tsx    # Registration form
│   ├── contexts/                # React Context providers
│   │   └── AuthContext.tsx     # Authentication state management
│   ├── api/                     # API client functions
│   │   ├── auth.ts             # Auth endpoints (login, register, logout)
│   │   ├── jobs.ts             # Jobs endpoints (list, search, refresh)
│   │   ├── matches.ts          # Matches endpoints (list, generate, update status)
│   │   ├── profile.ts          # Profile endpoints (get, update, CV upload)
│   │   ├── insights.ts         # Insights endpoints (skill analysis)
│   │   └── skills.ts           # Skills endpoints (popular, custom)
│   ├── types/                   # TypeScript type definitions
│   │   └── index.ts            # All app types (User, Job, Match, etc.)
│   ├── test/                    # Test configuration
│   │   └── setup.ts            # Vitest setup file
│   ├── App.tsx                  # Root component with routing
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles (Tailwind)
├── public/                      # Static assets
├── index.html                   # HTML template
├── vite.config.ts               # Vite configuration
├── vitest.config.ts             # Vitest test configuration
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies + scripts
└── .env                         # Environment variables (VITE_API_URL)
```

**Key Files:**
- `App.tsx` - Defines all routes, protected/public route logic
- `AuthContext.tsx` - Global auth state, login/logout, JWT token management
- `api/*.ts` - All HTTP API calls to backend (using axios)
- `components/__tests__/*.tsx` - Component tests using Vitest + React Testing Library

---

## Backend (`/backend`)

FastAPI application with SQLAlchemy ORM, Alembic migrations, and pytest tests.

```
backend/
├── app/
│   ├── main.py                  # FastAPI app initialization, CORS, middleware
│   ├── config.py                # Environment config (DB URL, API keys, JWT secret)
│   ├── database.py              # SQLAlchemy database connection + session management
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py         # Base model + all imports
│   │   ├── user.py             # User model (auth + profile)
│   │   ├── job.py              # Job model (with TSVectorType for search)
│   │   ├── match.py            # Match model (user-job matches)
│   │   ├── scrape_log.py       # ScrapeLog model (scraping tracking)
│   │   ├── skill_analysis.py   # SkillAnalysis model (market insights)
│   │   └── custom_skill.py     # CustomSkill model (user-contributed skills)
│   ├── routers/                 # API route handlers
│   │   ├── auth.py             # POST /auth/register, /login, /logout, GET /me
│   │   ├── jobs.py             # GET /api/jobs, /api/jobs/{id}, POST /api/jobs/refresh
│   │   ├── matches.py          # GET /api/matches, POST /matches/{id}/generate
│   │   ├── profile.py          # GET /api/profile, PUT /api/profile, POST /api/profile/cv
│   │   ├── insights.py         # GET /api/insights/skills
│   │   ├── skills.py           # GET /api/skills/popular, POST /api/skills/custom
│   │   └── health.py           # GET /health (healthcheck endpoint)
│   ├── services/                # Business logic services
│   │   ├── llm.py              # Claude API integration (CV parsing, job extraction)
│   │   ├── matching.py         # Job matching algorithm (score calculation)
│   │   ├── generation.py       # Cover letter + CV highlights generation
│   │   ├── insights.py         # Skill gap analysis + recommendations
│   │   ├── redis_cache.py      # Redis caching layer (LLM responses, etc.)
│   │   └── scraper.py          # Job saving + deduplication logic
│   ├── schemas/                 # Pydantic schemas (request/response validation)
│   │   ├── __init__.py
│   │   ├── auth.py             # LoginRequest, RegisterRequest, AuthResponse
│   │   ├── job.py              # JobResponse, JobScrapedData, JobFilters
│   │   └── profile.py          # ProfileUpdate, CVUploadResponse, ParsedCV
│   ├── dependencies/            # FastAPI dependencies
│   │   └── auth.py             # get_current_user (JWT authentication)
│   └── utils/                   # Utility functions
│       ├── auth.py             # Password hashing, JWT token creation/verification
│       └── cv_parser.py        # Extract text from PDF, DOCX, TXT files
├── migrations/                  # Alembic database migrations
│   ├── env.py                  # Alembic environment configuration
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration version files
│       ├── 6aba7fe40207_initial_migration_jobs_users_matches_.py
│       ├── 054a4f72cc3b_add_unique_constraint_on_source_and_.py
│       ├── 45bdbd9c1063_add_skill_analysis_table.py
│       ├── 5b6fab1826e2_add_scrape_logs_table.py
│       ├── 79d767eb5024_add_performance_indexes.py
│       ├── b9152b597093_add_fulltext_search_index.py
│       ├── c1540e330578_add_composite_indexes_for_matches.py
│       └── a246a7dfd293_add_custom_skills_table.py
├── tests/                       # Test suite (pytest)
│   ├── conftest.py             # Test fixtures (db_session, client, test_user, etc.)
│   ├── unit/                   # Unit tests
│   │   ├── test_llm_service.py
│   │   └── test_auth_utils.py
│   └── integration/            # Integration tests
│       ├── test_auth_router.py
│       ├── test_jobs_router.py
│       ├── test_matches_router.py
│       ├── test_profile_router_updated.py
│       └── test_scraper_service.py
├── .env                        # Environment variables (DB URL, API keys)
├── alembic.ini                 # Alembic configuration
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── .venv/                      # Python virtual environment (gitignored)
```

**Key Files:**
- `main.py` - FastAPI app setup, router registration, CORS configuration, startup/shutdown events
- `config.py` - Reads from `.env` file, validates required settings
- `database.py` - Creates SQLAlchemy engine + session factory
- `dependencies/auth.py` - JWT token verification, extracts current user from request
- `services/llm.py` - All Claude API calls (with Redis caching)
- `services/matching.py` - Core matching algorithm (skill/title/experience scoring)
- `tests/conftest.py` - Shared test fixtures (database, authenticated client, etc.)

---

## Scraping (`/scraping`)

Python scripts for scraping job boards.

```
scraping/
├── scrapers/
│   ├── __init__.py
│   ├── remoteok.py             # RemoteOK scraper (JSON API)
│   └── weworkremotely.py       # WeWorkRemotely scraper (placeholder)
└── README.md
```

**Usage:**
```bash
cd scraping
source ../backend/.venv/bin/activate
python -m scrapers.remoteok
```

---

## Infrastructure (`/infrastructure`)

Terraform configuration for deployment to Railway and Vercel.

```
infrastructure/
└── terraform/
    ├── main.tf                 # Main Terraform configuration
    ├── variables.tf            # Input variables
    ├── outputs.tf              # Output values
    ├── providers.tf            # Provider configuration (Railway, Vercel)
    ├── dev.tfvars              # Development environment variables (gitignored)
    └── .terraform/             # Terraform state (gitignored)
```

**Managed Resources:**
- Railway: Project, PostgreSQL service, Redis service, Backend service
- Vercel: Frontend project (connected to GitHub)

---

## Documentation (`/docs`)

Project documentation files.

```
docs/
├── ROADMAP.md                  # Project roadmap, phases, tasks
├── SCHEMA.md                   # Database schema documentation
└── FILE_STRUCTURE.md           # This file
```

---

## Root Files

```
career-agent/
├── docker-compose.yml          # Local development (Postgres + Redis)
├── package.json                # Yarn workspace configuration + root scripts
├── .gitignore                  # Git ignore patterns
├── .env.example                # Example environment variables
└── README.md                   # Project overview + setup instructions
```

**Root package.json scripts:**
```bash
yarn dev              # Start frontend + backend concurrently
yarn frontend:dev     # Start frontend only
yarn backend:dev      # Start backend only
yarn backend:setup    # Create Python venv + install dependencies
yarn db:up            # Start Postgres + Redis (docker-compose)
yarn db:down          # Stop Postgres + Redis
yarn db:migrate       # Run Alembic migrations
yarn scraping:run     # Run RemoteOK scraper
yarn lint             # Run ESLint on frontend
yarn build            # Build frontend for production
```

---

## Environment Files

### Backend `.env`

Required environment variables for backend:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/career_agent
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# External APIs
ANTHROPIC_API_KEY=sk-ant-...

# Environment
ENVIRONMENT=development
```

### Frontend `.env`

Required environment variables for frontend:

```bash
VITE_API_URL=http://localhost:8000
```

---

## Testing Structure

### Backend Tests

**Organization:**
- `tests/unit/` - Pure unit tests (mocked dependencies)
- `tests/integration/` - Integration tests (real database, FastAPI TestClient)
- `tests/conftest.py` - Shared fixtures

**Test Database:**
- Uses in-memory SQLite for fast test execution
- Custom `TSVectorType` handles PostgreSQL/SQLite differences
- Each test gets isolated database session

**Coverage:** 60% overall, 75%+ on critical services

### Frontend Tests

**Organization:**
- `src/components/__tests__/` - Component tests
- `src/test/setup.ts` - Test configuration

**Tools:**
- Vitest (test runner)
- React Testing Library (component testing)
- jsdom (browser environment simulation)

**Coverage:** Basic coverage of key components (JobCard, ProtectedRoute)

---

## Gitignore Highlights

**Ignored files/directories:**
- `backend/.venv/` - Python virtual environment
- `backend/.env` - Backend secrets
- `frontend/.env` - Frontend config
- `frontend/node_modules/` - Node dependencies
- `node_modules/` - Root node modules
- `**/__pycache__/` - Python cache
- `*.pyc` - Compiled Python files
- `htmlcov/` - Test coverage reports
- `.pytest_cache/` - Pytest cache
- `infrastructure/terraform/.terraform/` - Terraform state
- `infrastructure/terraform/*.tfvars` - Terraform variables

---

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Query |
| Backend | Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL 17 (production), SQLite (tests) |
| Cache | Redis 7 |
| LLM | Anthropic Claude (Haiku for extraction, Sonnet for generation) |
| Testing | Pytest + Vitest + React Testing Library |
| Infrastructure | Terraform, Railway, Vercel |
| Scraping | httpx (RemoteOK API) |
| Auth | JWT (7-day expiry), bcrypt password hashing |

---

## Development Workflow

1. **Start databases:** `yarn db:up`
2. **Run migrations:** `yarn db:migrate`
3. **Start dev servers:** `yarn dev` (starts both frontend + backend)
4. **Run tests:**
   - Backend: `cd backend && pytest`
   - Frontend: `cd frontend && yarn test`
5. **Create migration:** `cd backend && alembic revision --autogenerate -m "description"`
6. **Run scraper:** `yarn scraping:run`

---

## Port Allocation

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI) | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## Recent Changes

- **2025-12-18:** Added `custom_skills` table, Vitest test setup, TSVectorType for cross-DB compatibility
- **2025-12-17:** Added composite indexes on matches, skill autocomplete modal
- **2025-12-16:** Added full-text search with PostgreSQL TSVECTOR + GIN index
- **2025-12-13:** Added scrape_logs and skill_analysis tables
- **2025-12-12:** Initial migration with users, jobs, matches tables
