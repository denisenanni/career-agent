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
- **Database**: PostgreSQL (Neon)
- **Cache**: Redis (Upstash)
- **LLM**: Anthropic Claude
- **Scraping**: Playwright
- **Infrastructure**: Terraform (Neon, Upstash, Fly.io, Vercel)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Yarn

### Local Development

```bash
# 1. Clone the repo
git clone https://github.com/denisenanni/career-agent.git
cd career-agent

# 2. Install frontend dependencies
yarn install

# 3. Set up backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 4. Copy environment variables
cp .env.example .env
# Edit .env with your values

# 5. Start local services (Postgres, Redis)
docker-compose up -d

# 6. Run migrations
yarn db:migrate

# 7. Start development servers
yarn dev
```

Frontend: http://localhost:5173
Backend: http://localhost:8000
API Docs: http://localhost:8000/docs

### Testing the Scraper

```bash
cd scraping
source ../backend/.venv/bin/activate
python -m scrapers.remoteok
```

## Infrastructure

### Deploy with Terraform

```bash
cd infrastructure/terraform

# Copy and fill in variables
cp terraform.tfvars.example dev.tfvars

# Initialize
terraform init

# Plan
terraform plan -var-file=dev.tfvars

# Apply
terraform apply -var-file=dev.tfvars
```

### Manual Deployment

**Backend (Fly.io)**:
```bash
cd backend
fly launch  # First time
fly deploy  # Updates
```

**Frontend (Vercel)**:
Push to main branch - auto deploys via Vercel GitHub integration.

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
