# Career Agent

An AI-powered job hunting assistant that:
1. Scrapes job boards for relevant postings
2. Matches jobs against your CV and preferences
3. Generates tailored cover letters and CV highlights
4. Tracks applications and provides insights

**Repository:** https://github.com/denisenanni/career-agent
**Live App:** https://career-agent-dev.vercel.app/

## Features

- 🔍 **Job Scraping** - Automatically scrapes RemoteOK, WeWorkRemotely, and more
- 📄 **CV Parsing** - Upload your CV and extract skills/experience with Claude AI
- 🎯 **Smart Matching** - AI-powered job ranking based on skills, experience, and preferences
- ✍️ **Application Generation** - Generate personalized cover letters and tailored CV highlights
- 📊 **Career Insights** - Market analysis and skill recommendations based on job trends
- 📋 **Application Tracking** - Track your application status (matched, interested, applied)

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind
- **Backend**: Python FastAPI
- **Database**: PostgreSQL 17 (Docker for local, Railway for production)
- **Cache**: Redis (Docker for local, Railway for production)
- **LLM**: Anthropic Claude (Haiku for extraction, Sonnet for generation)
- **Scraping**: httpx + BeautifulSoup
- **Infrastructure**: Docker Compose (local), Terraform + Railway + Vercel (production)

## Quick Start

```bash
# 1. Install dependencies
yarn install

# 2. Start Docker services (PostgreSQL + Redis)
docker-compose up -d

# 3. Run database migrations
yarn db:migrate

# 4. Start dev servers (frontend + backend)
yarn dev
```

Visit http://localhost:5173 and register an account!

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Yarn

### Local Development

#### 1. Clone and Install Dependencies

```bash
# Clone the repo
git clone https://github.com/denisenanni/career-agent.git
cd career-agent

# Install frontend dependencies
yarn install

# Set up backend virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

#### 2. Configure Environment Variables

The backend `.env` file is already configured at `backend/.env` with:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Database credentials: `career_agent` / `career_agent_dev`

If you need to change these, edit `backend/.env`.

#### 3. Start Database Services

**IMPORTANT: You must start Docker containers before running the backend!**

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify containers are running
docker-compose ps

# You should see:
# career-agent-db     postgres:17-alpine     Up
# career-agent-redis  redis:7-alpine         Up
```

#### 4. Run Database Migrations

```bash
# Create database tables
yarn db:migrate

# OR manually:
cd backend
source .venv/bin/activate
alembic upgrade head
cd ..
```

#### 5. Start Development Servers

**Option A - Start both frontend and backend:**
```bash
yarn dev
```

**Option B - Start separately:**
```bash
# Terminal 1 - Backend
yarn backend:dev

# Terminal 2 - Frontend
yarn frontend:dev
```

#### 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Troubleshooting

#### Database Connection Errors

If you see `Connection refused` or `password authentication failed`:

1. **Check Docker is running:**
```bash
docker ps
# Should show career-agent-db and career-agent-redis
```

2. **Start containers if not running:**
```bash
docker-compose up -d
```

3. **Check container logs:**
```bash
docker-compose logs postgres
docker-compose logs redis
```

4. **Verify connection:**
```bash
# Test PostgreSQL connection
docker exec -it career-agent-db psql -U career_agent -d career_agent -c "SELECT 1;"

# Test Redis connection
docker exec -it career-agent-redis redis-cli ping
```

5. **Restart everything:**
```bash
docker-compose down
docker-compose up -d
yarn db:migrate
yarn backend:dev
```

#### Port Already in Use

If ports 5432, 6379, 8000, or 5173 are in use:

```bash
# Find and kill process using port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # PostgreSQL
```

#### Migration Errors

If migrations fail:

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
yarn db:migrate
```

### Testing the Scraper

```bash
cd scraping
source ../backend/.venv/bin/activate
python -m scrapers.remoteok
```

### Common Commands

```bash
# Local development
docker-compose up -d          # Start Postgres + Redis
yarn install                  # Install frontend deps
yarn backend:setup            # Set up Python venv
yarn dev                      # Start frontend + backend

# Database
yarn db:migrate               # Run migrations
alembic revision --autogenerate -m "description"  # Create migration

# Testing
cd backend && pytest          # Run backend tests
cd frontend && yarn test      # Run frontend tests

# Scraping
cd scraping
python -m scrapers.remoteok   # Test RemoteOK scraper
```

---

## Deployment

### Production Infrastructure (Terraform)

Deploy to Railway (backend + database) and Vercel (frontend):

```bash
cd infrastructure/terraform

# Copy and fill in variables
cp terraform.tfvars.example dev.tfvars
# Add: RAILWAY_TOKEN, VERCEL_TOKEN, ANTHROPIC_API_KEY, JWT_SECRET

# Initialize
terraform init

# Plan
terraform plan -var-file=dev.tfvars

# Apply
terraform apply -var-file=dev.tfvars
```

**What gets deployed:**
- Railway Project with PostgreSQL, Redis, and FastAPI backend
- Vercel Project with React frontend
- Environment variables configured automatically

### Manual Deployment

**Backend (Railway)**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Deploy
railway up
```

**Frontend (Vercel)**:
- Push to `main` branch - auto deploys via Vercel GitHub integration
- Or deploy manually: `vercel --prod`

### Environment Variables

**Required for Production:**
- `DATABASE_URL` - Auto-injected by Railway PostgreSQL
- `REDIS_URL` - Auto-injected by Railway Redis
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `JWT_SECRET` - Generate with `openssl rand -base64 32`
- `ENVIRONMENT` - Set to `production`

## Project Structure

Monorepo with separate frontend, backend, scraping scripts, and infrastructure code.

**Main Directories:**
- **`frontend/`** - React + TypeScript + Vite (UI components, pages, API clients)
- **`backend/`** - Python FastAPI (API routers, models, services, migrations, tests)
- **`scraping/`** - Job board scrapers (RemoteOK, WeWorkRemotely, etc.)
- **`infrastructure/`** - Terraform configuration for Railway + Vercel
- **`docs/`** - Complete project documentation
- **`docker-compose.yml`** - PostgreSQL + Redis for local development

See **[FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md)** for complete directory trees with detailed file-by-file descriptions.

## Documentation

- **[ROADMAP.md](docs/ROADMAP.md)** - Project phases, implementation plan, and progress tracking
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture, components, data flows, infrastructure, and costs
- **[API.md](docs/API.md)** - Complete API reference with examples and authentication
- **[SCHEMA.md](docs/SCHEMA.md)** - Database schema, tables, indexes, and relationships
- **[FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md)** - Project directory structure and organization
- **[DEV_NOTES.md](docs/DEV_NOTES.md)** - Development notes, conventions, debugging tips, and future features

## License

MIT
