# Career Agent

AI-powered job hunting assistant that scrapes job boards, matches jobs to your profile, and generates tailored applications.

## Features

- 🔍 **Job Scraping** - Automatically scrapes RemoteOK, WeWorkRemotely, and more
- 📄 **CV Parsing** - Upload your CV and extract skills/experience
- 🎯 **Smart Matching** - AI ranks jobs by compatibility with your profile
- ✍️ **Application Generation** - Generate tailored cover letters and CV highlights
- 📊 **Application Tracking** - Track your application status

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

```
career-agent/
├── frontend/           # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types/
│   └── ...
├── backend/            # Python FastAPI
│   ├── app/
│   │   ├── routers/
│   │   ├── models/
│   │   ├── services/
│   │   └── ...
│   └── requirements.txt
├── scraping/           # Job scrapers
│   └── scrapers/
├── shared/             # Shared TypeScript types
├── infrastructure/     # Terraform configs
│   └── terraform/
├── docs/               # Documentation
│   └── ROADMAP.md
└── docker-compose.yml  # Local dev services
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed roadmap and architecture.

## License

MIT
