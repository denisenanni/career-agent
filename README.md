# Career Agent

An AI-powered job hunting assistant that automates job discovery, matching, and application preparation.

**Repository:** https://github.com/denisenanni/career-agent
**Live App:** https://career-agent-dev.vercel.app/

## Overview

Career Agent helps job seekers by:

1. Scraping job boards for relevant postings
2. Matching jobs against your CV and preferences using AI
3. Generating tailored cover letters and CV highlights
4. Tracking applications and providing market insights

## Features

- **Job Scraping** - Automatically aggregates jobs from RemoteOK, WeWorkRemotely, HackerNews, and more
- **CV Parsing** - Upload PDF/DOCX/TXT and extract skills, experience, and contact info using Claude AI
- **Smart Matching** - AI-powered job ranking based on skills overlap, experience level, salary, and preferences
- **Application Materials** - Generate personalized cover letters and tailored CV bullet points per job
- **Market Analysis** - Skill demand trends and recommendations based on current job postings
- **Application Tracking** - Track status progression (matched, interested, applied, hidden)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 17 |
| Cache | Redis 7 |
| AI/LLM | Anthropic Claude (Haiku for extraction, Sonnet for generation) |
| Scraping | httpx, BeautifulSoup, defusedxml |
| Infrastructure | Docker Compose (local), Terraform, Railway, Vercel |
| Testing | pytest (backend), Vitest (frontend) |

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/denisenanni/career-agent.git
cd career-agent
yarn install

# 2. Start database services
docker-compose up -d

# 3. Run migrations
yarn db:migrate

# 4. Start development servers
yarn dev
```

Access the app at http://localhost:5173

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- Yarn

## Local Development

### Installation

```bash
# Install frontend dependencies
yarn install

# Set up backend virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### Configuration

The backend `.env` file at `backend/.env` is pre-configured for local development:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Database: `career_agent` / `career_agent_dev`

For production, you'll need to add:
- `ANTHROPIC_API_KEY` - From https://console.anthropic.com/
- `JWT_SECRET` - Generate with `openssl rand -base64 32`

### Starting Services

```bash
# Start PostgreSQL and Redis containers
docker-compose up -d

# Verify containers are running
docker-compose ps

# Run database migrations
yarn db:migrate

# Start both frontend and backend
yarn dev
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Testing

```bash
# Backend tests
cd backend
source .venv/bin/activate
pytest

# Frontend tests
cd frontend
yarn test
```

## Project Structure

```
career-agent/
├── frontend/          # React + TypeScript application
├── backend/           # FastAPI application
│   ├── app/           # Application code (routers, models, services)
│   ├── migrations/    # Alembic database migrations
│   └── tests/         # pytest test suites
├── scraping/          # Job board scrapers
├── infrastructure/    # Terraform configurations
├── docs/              # Project documentation
└── docker-compose.yml # Local development services
```

## API Rate Limits

The following endpoints have rate limits to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| POST /api/auth/register | 5/hour |
| POST /api/auth/login | 10/minute |
| POST /api/profile/cv | 10/hour |
| POST /api/user-jobs/parse | 10/hour |

## Deployment

### Infrastructure (Terraform)

Deploy to Railway (backend, PostgreSQL, Redis) and Vercel (frontend):

```bash
cd infrastructure/terraform
cp terraform.tfvars.example dev.tfvars
# Edit dev.tfvars with your tokens and secrets

terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

### Manual Deployment

**Backend (Railway):**
```bash
railway login
railway link
railway up
```

**Frontend (Vercel):**
- Automatic deployment on push to `main` branch
- Manual: `vercel --prod`

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string (auto-injected by Railway) |
| REDIS_URL | Redis connection string (auto-injected by Railway) |
| ANTHROPIC_API_KEY | Anthropic API key for Claude |
| JWT_SECRET | Secret key for JWT token signing |
| ENVIRONMENT | `development` or `production` |

## Documentation

- [ROADMAP.md](docs/ROADMAP.md) - Project phases and progress
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and data flows
- [API.md](docs/API.md) - Complete API reference
- [SCHEMA.md](docs/SCHEMA.md) - Database schema documentation
- [FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md) - Directory organization
- [DEV_NOTES.md](docs/DEV_NOTES.md) - Development conventions and tips

## Troubleshooting

### Database Connection Issues

```bash
# Check if containers are running
docker ps

# View container logs
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose down
docker-compose up -d
yarn db:migrate
```

### Port Conflicts

```bash
# Kill process on specific port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### Reset Database

```bash
# Warning: This deletes all data
docker-compose down -v
docker-compose up -d
yarn db:migrate
```

## License

MIT
