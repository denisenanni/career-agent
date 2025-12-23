# Development Notes

Quick reference for development workflow, technical decisions, and debugging tips.

**For project roadmap and future features, see [ROADMAP.md](./ROADMAP.md)**

---

## Development Workflow

### Stack Reminder
- **Frontend:** React + TypeScript + Vite → `yarn` (NOT npm)
- **Backend:** Python FastAPI → Alembic migrations, Pydantic validation
- **LLMs:** Haiku for extraction, Sonnet for generation
- **Database:** PostgreSQL (no `any` types - build proper types)

### Before Making Changes
1. Check ROADMAP.md for current phase
2. Verify approach with team/lead first
3. Complete tasks, mark [x] when done
4. Keep changes minimal and focused
5. Check existing dependencies before installing new ones

### Common Commands

```bash
# Local Development
docker-compose up -d          # Start Postgres + Redis
yarn install                  # Install frontend deps (frontend/ directory)
yarn backend:setup            # Set up Python venv
yarn dev                      # Start frontend + backend concurrently

# Database
yarn db:migrate               # Run Alembic migrations
cd backend && alembic revision --autogenerate -m "description"  # Create migration
cd backend && alembic current # Check current migration
cd backend && alembic upgrade head  # Apply pending migrations

# Testing
cd backend && pytest                    # Run all backend tests
cd backend && pytest tests/unit/        # Run unit tests only
cd backend && pytest -v -k "test_name"  # Run specific test
cd frontend && yarn test                # Run frontend tests
cd frontend && yarn test:ui             # Run tests with UI
cd frontend && yarn build               # Build frontend

# Terraform (Deployment)
cd infrastructure/terraform
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars

# Manual Scraping (Testing)
cd backend && python -m app.services.scraper
```

---

## LLM Usage Guidelines

**Cost Optimization is Critical:**
- **Haiku 4.5:** Cheap, fast → Use for extraction (CV parsing, job requirements)
- **Sonnet 4.5:** Expensive, high quality → Use for generation (cover letters, match analysis)
- **Always cache LLM results:** Redis with 30-day TTL for generated content
- **Current cache hit rate:** ~90% (saves significant API costs)

**Cache Strategy:**
| Content Type | Model | TTL | Cost per call | Cache savings |
|--------------|-------|-----|--------------|---------------|
| CV Parsing | Haiku | 30d | ~$0.01 | Free on hit |
| Job Extraction | Haiku | 7d | ~$0.005 | Free on hit |
| Cover Letter | Sonnet | 30d | ~$0.15 | Free on hit |
| CV Highlights | Haiku | 30d | ~$0.01 | Free on hit |

**Never:**
- Use Sonnet for simple extraction tasks
- Skip caching (always cache LLM responses)
- Make redundant LLM calls (check cache first)

---

## Data Sources

### RemoteOK
- **API:** `https://remoteok.com/api`
- **Format:** JSON (no auth required)
- **Volume:** ~500 jobs per scrape
- **Status:** ✅ Implemented and working

### Future Job Boards
See [ROADMAP.md](./ROADMAP.md#phase-8-post-production-features-future) for planned scrapers.

---

## Code Conventions

### Python (Backend)
- Use type hints everywhere (`def func(user: User) -> Dict[str, Any]`)
- Pydantic models for all API requests/responses
- Services handle business logic, routers handle HTTP
- Always use dependency injection (`Depends(get_db)`)
- Cache LLM calls with Redis
- Use Alembic for all schema changes (never modify DB directly)

### TypeScript (Frontend)
- **NO `any` types** - build proper interfaces
- Use React Query for all API calls (built-in caching)
- Components in `PascalCase`, files in `PascalCase.tsx`
- API functions in `camelCase`
- Use `yarn` not `npm`

### SQL/Alembic
- Always create migrations with `--autogenerate`
- Review generated SQL before applying
- Add indexes for foreign keys and frequently queried columns
- Use `ON DELETE CASCADE` for dependent data

---

## Ask Before...

**Always ask before:**
- Creating Alembic migrations (schema changes)
- Deleting files or code
- Installing new dependencies
- Editing .env or Terraform configs
- Running `git push`
- Destructive database operations
- `sudo` commands

**Never do without asking:**
- `rm -rf`
- `git push --force`
- `DROP TABLE` / `DROP DATABASE`
- `terraform destroy`

---

## Quick Debugging

### Database Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View logs
docker-compose logs postgres

# Connect to database
docker exec -it career-agent-postgres psql -U career_agent

# Reset database (⚠️ DELETES ALL DATA)
docker-compose down -v
docker-compose up -d
cd backend && alembic upgrade head
```

### Redis Issues

```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
docker exec -it career-agent-redis redis-cli ping

# Clear cache
docker exec -it career-agent-redis redis-cli FLUSHALL
```

### Backend Issues

```bash
# Check backend logs
docker-compose logs backend

# Run specific test
cd backend && pytest tests/integration/test_matches_router.py -v

# Check database connection
cd backend && python -c "from app.database import engine; print(engine.url)"
```

### Frontend Issues

```bash
# Clear node_modules and reinstall
rm -rf node_modules yarn.lock
yarn install

# Check build
yarn build

# Run with verbose logging
yarn dev --debug
```

---

## Environment Setup Checklist

### First Time Setup
- [ ] Clone repository
- [ ] Copy `.env.example` to `.env` and fill in values
- [ ] Start Docker: `docker-compose up -d`
- [ ] Install frontend deps: `yarn install`
- [ ] Set up backend venv: `yarn backend:setup`
- [ ] Run migrations: `yarn db:migrate`
- [ ] Start dev servers: `yarn dev`
- [ ] Test scraper: `cd backend && python -m app.services.scraper`

### After Pulling Changes
- [ ] Check for new dependencies: `yarn install` + `cd backend && pip install -r requirements.txt`
- [ ] Run new migrations: `yarn db:migrate`
- [ ] Restart services if needed

---

## Recent Completed Work

**For detailed implementation history, see [ROADMAP.md](./ROADMAP.md)**

### Latest (December 19, 2024)
- ✅ Removed work_type from match scoring (now hard filter only)
- ✅ Fixed test failures (35 → 26 failing)
- ✅ Disabled rate limiting in tests
- ✅ Fixed frontend build (excluded test files from TSC)
- ✅ Email allowlist comprehensive test suite (27 tests)

### Recent Major Features
- ✅ UI Polish - Loading states, error handling, mobile responsive
- ✅ User-Submitted Jobs - Paste custom job postings
- ✅ Employment Eligibility Filter - Geographic/visa restrictions
- ✅ Email Allowlist System - Control registration with admin API
- ✅ Security Hardening - JWT validation, rate limiting, CORS
- ✅ Comprehensive Testing - 138+ tests (frontend + backend)

**See full history in [ROADMAP.md](./ROADMAP.md) Phase 7 sections.**

---

## Useful Links

- **Local Development:**
  - Backend API: http://localhost:8000
  - Swagger Docs: http://localhost:8000/docs
  - Redoc: http://localhost:8000/redoc
  - Frontend: http://localhost:5173

- **Documentation:**
  - [README.md](../README.md) - Quick start guide
  - [ROADMAP.md](./ROADMAP.md) - Project phases and future features
  - [ARCHITECTURE.md](./ARCHITECTURE.md) - Infrastructure and deployment
  - [SCHEMA.md](./SCHEMA.md) - Database schema details
  - [API.md](./API.md) - Complete API reference

- **Repository:**
  - GitHub: https://github.com/denisenanni/career-agent

---

## Git Workflow

```bash
# Standard workflow
git status                    # Check changes
git add .                     # Stage all changes
git commit -m "feat: description"  # Commit with message
git push                      # Push to remote

# Commit message format
# feat: new feature
# fix: bug fix
# docs: documentation
# test: add/update tests
# refactor: code cleanup
# chore: maintenance
```

---

## Performance Tips

- **React Query:** Automatic caching, refetch on window focus (5min stale time)
- **Redis:** Cache all LLM calls (90% hit rate = major cost savings)
- **Database:** Full-text search with PostgreSQL `tsvector` + GIN index
- **Frontend:** Code splitting with React.lazy() for faster initial load
- **Rate Limiting:** Protects against abuse and runaway API costs

---

## UI/UX Patterns

### Auto-Save
Profile forms (PreferencesForm, ParsedCVDisplay) use auto-save with debounce:
- **Hook:** `useAutoSave` in `src/hooks/useAutoSave.ts`
- **Debounce:** 1.5 seconds after last change
- **Status indicator:** Shows "Saving..." → "✓ Saved" → (fades after 2s)
- **No save button needed** - changes persist automatically

```typescript
const { status, error } = useAutoSave({
  data: formData,
  onSave: async (data) => { await updateProfile(data) },
  debounceMs: 1500,
  enabled: isInitialized,
})
```

---

## Technical Debt

See current technical debt tracked in ROADMAP.md.
---

## Security Checklist

**Always verify:**
- [ ] No secrets in code (use .env)
- [ ] No `any` types that bypass validation
- [ ] Input validation on all API endpoints
- [ ] SQL injection protection (use SQLAlchemy ORM)
- [ ] XSS protection (React escapes by default)
- [ ] Authentication on protected routes
- [ ] Rate limiting on expensive operations
- [ ] CORS configured correctly for production

---

## Common Gotchas

1. **Frontend:** Always use `yarn`, not `npm` (workspace project)
2. **Backend:** Always create migrations, never modify schema directly
3. **Tests:** Backend tests need `TEST_DATABASE_URL` env var for PostgreSQL
4. **TypeScript:** Excluding `*.test.ts` files from build (in tsconfig.json)
5. **LLM Costs:** Always check cache before making Claude API call
6. **Git:** Never force push to main branch

---

**For roadmap, pending features, and future plans → [ROADMAP.md](./ROADMAP.md)**

