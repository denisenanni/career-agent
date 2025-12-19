# Development Notes

Quick reference and development reminders for Career Agent.

---

## LLM Usage Guidelines

- **Use Haiku for extraction** (cheap) - CV parsing, job requirement extraction
- **Use Sonnet for generation** (quality) - Cover letters, match analysis
- **Cache LLM results aggressively** - Redis caching with 30-day TTL for generated content
- Current cache hit rate: ~90% (significant cost savings)

---

## Data Sources

### RemoteOK
- **API:** `https://remoteok.com/api`
- **Format:** JSON (no auth required)
- **Volume:** ~500 jobs per scrape
- **Features:** Tags for skills, salary info, remote-first focus
- **Status:** ✅ Implemented

### WeWorkRemotely
- **Method:** HTML scraping with BeautifulSoup
- **Difficulty:** Medium
- **Status:** 🚧 Planned

### LinkedIn
- **Method:** Requires authentication, anti-scraping measures
- **Difficulty:** High
- **Status:** 📋 Future/Stretch goal (save for later)

---

## Development Workflow

### Before Deploying
- [ ] Test locally with `yarn dev`
- [ ] Run backend tests: `cd backend && pytest`
- [ ] Run frontend tests: `cd frontend && yarn test`
- [ ] Check migrations: `alembic current` and `alembic upgrade head`
- [ ] Verify .env variables are not committed
- [ ] Review git status and commit frequently

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

## Future Features & Ideas

### Streaming with Claude API
**Question:** Do we use streaming with Claude chats? If not, is it worth implementing?

**Considerations:**
- Current implementation uses synchronous API calls
- Streaming could improve UX for long cover letter generation
- Would require frontend changes (streaming UI, SSE or WebSockets)
- Trade-off: Added complexity vs improved perceived performance

**Decision:** Defer until user feedback indicates slow generation is a pain point

---

### API Documentation with Redoc
**Status:** ✅ Already available!

FastAPI automatically provides both:
- **Swagger UI**: http://localhost:8000/docs (interactive, test endpoints)
- **Redoc**: http://localhost:8000/redoc (clean, readable, better for documentation)

Both are generated from the same OpenAPI schema and stay in sync automatically.

**Reference:** See [API.md](./API.md) for complete API documentation

---

### User-Submitted Job Postings

**Feature Request:** Allow users to paste job ads that didn't come from scraped listings

**Requirements:**
1. Parse pasted job text (title, company, description, requirements)
2. Store in new entity: `user_jobs` table (user-specific, not shared)
3. Perform same AI analysis as scraped jobs:
   - Extract requirements with Claude Haiku
   - Generate match score
   - Identify skill gaps
   - Generate cover letter/CV highlights
4. Display in separate section (not mixed with scraped jobs)
5. UI placement options:
   - New menu item: "My Jobs" or "Custom Jobs"
   - Section within Profile page
   - Tab in Jobs page (e.g., "All Jobs" | "My Jobs")

**Implementation Notes:**
- Similar to CV parsing flow (paste → extract → store)
- Reuse existing matching and generation services
- Add `is_user_submitted` flag or separate table
- Consider allowing users to edit extracted fields

**Priority:** Medium (after Phase 6 deployment)

**Database Schema:**
```sql
CREATE TABLE user_jobs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255),
  description TEXT NOT NULL,
  url VARCHAR(500),  -- optional, if user provides one
  source VARCHAR(50) DEFAULT 'user_submitted',

  -- Extracted by Claude (same as scraped jobs)
  tags JSONB DEFAULT '[]',
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10),
  location VARCHAR(255),
  remote_type VARCHAR(50),
  job_type VARCHAR(50),

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- No source_id needed (user-specific)
  UNIQUE(user_id, company, title)  -- Prevent duplicates per user
);
```

**API Endpoints:**
```
POST /api/user-jobs           - Submit new job from pasted text
GET /api/user-jobs            - List user's submitted jobs
GET /api/user-jobs/{id}       - Get job details
PUT /api/user-jobs/{id}       - Update job (allow editing)
DELETE /api/user-jobs/{id}    - Delete user job
```

**LLM Prompt for Parsing:**
```
Extract job information from this pasted job posting. Return JSON only.

{
  "title": "string",
  "company": "string or null",
  "description": "cleaned description text",
  "location": "string or null",
  "remote_type": "full" | "hybrid" | "onsite" | null,
  "job_type": "permanent" | "contract" | "part-time" | null,
  "salary_min": number or null,
  "salary_max": number or null,
  "salary_currency": "USD" | "EUR" | etc,
  "required_skills": ["skill1", "skill2", ...],
  "nice_to_have_skills": ["skill1", ...],
  "experience_years_min": number or null
}

Pasted Job Text:
---
{user_input}
```

---

## Performance Monitoring

### Metrics to Track (Future)
- Redis cache hit rate (target: >90%)
- Claude API cost per user per month
- Average job match generation time
- Database query performance (slow query log)
- Frontend bundle size and load time

### Current Performance
- LLM cache hit rate: ~90% ✅
- Full-text search: 5ms avg (95% faster than before) ✅
- Cover letter generation: 2-5s (first time), <50ms (cached) ✅
- Backend test coverage: 60% ✅
- Frontend test coverage: Initial setup complete ✅

---

## Technical Debt

### High Priority
- None currently blocking

### Medium Priority
- Add CI/CD pipeline (GitHub Actions)
- Increase backend test coverage to 80%
- Add more frontend component tests
- Set up error tracking (Sentry)
- Add monitoring/observability (Railway metrics)

### Low Priority
- Consider batch job analysis to reduce LLM calls
- Add Redis cluster for production HA (Railway handles this)
- Optimize JWT to reduce DB lookups (add user info to token payload)
- Add database read replicas for analytics (only needed at scale)

---

## Dependencies to Watch

### Security Updates
- Check `pip list --outdated` and `yarn outdated` regularly
- Update Anthropic SDK when new features released
- Monitor FastAPI and React releases

### Breaking Changes
- Railway provider version bumps
- PostgreSQL major version upgrades (17 → 18)
- Claude API changes (model deprecations)

---

## Useful Links

- **Anthropic API Docs:** https://docs.anthropic.com/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Query Docs:** https://tanstack.com/query/latest
- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **Railway Docs:** https://docs.railway.app/
- **Vercel Docs:** https://vercel.com/docs

---

## Git Workflow Reminders

- **Commit frequently** - Small, focused commits
- **Test locally first** - Run tests before pushing
- **Migration workflow:**
  1. Make model changes
  2. Generate migration: `alembic revision --autogenerate -m "description"`
  3. Review migration file manually
  4. Test migration: `alembic upgrade head`
  5. Test rollback: `alembic downgrade -1` then `alembic upgrade head`
  6. Commit migration file

---

## Environment Setup Checklist

### First Time Setup
- [ ] Clone repo
- [ ] `yarn install`
- [ ] `cd backend && python -m venv .venv`
- [ ] `source .venv/bin/activate && pip install -r requirements.txt`
- [ ] Copy `backend/.env.example` to `backend/.env` (if exists)
- [ ] `docker-compose up -d`
- [ ] `yarn db:migrate`
- [ ] Get Anthropic API key from https://console.anthropic.com/
- [ ] Add `ANTHROPIC_API_KEY` to `backend/.env`
- [ ] `yarn dev`

### After Pulling Changes
- [ ] `yarn install` (if package.json changed)
- [ ] `cd backend && pip install -r requirements.txt` (if requirements.txt changed)
- [ ] `yarn db:migrate` (if new migrations)
- [ ] Restart dev servers

---

## Quick Debugging

### Database Issues
```bash
# Check if PostgreSQL is running
docker ps | grep career-agent-db

# View logs
docker-compose logs postgres

# Connect to database
docker exec -it career-agent-db psql -U career_agent -d career_agent

# Reset database (⚠️ DELETES ALL DATA)
docker-compose down -v
docker-compose up -d
yarn db:migrate
```

### Redis Issues
```bash
# Check if Redis is running
docker ps | grep career-agent-redis

# Test connection
docker exec -it career-agent-redis redis-cli ping

# Clear cache
docker exec -it career-agent-redis redis-cli FLUSHALL
```

### Backend Issues
```bash
# Check backend logs
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --log-level debug

# Run specific test
pytest tests/unit/test_llm_service.py -v

# Check database connection
python -c "from app.database import engine; print(engine.url)"
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

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use `ruff` for linting
- Type hints required for function signatures
- Docstrings for public functions (Google style)
- Max line length: 100 characters

### TypeScript (Frontend)
- Use `eslint` and `prettier`
- No `any` types - build proper types
- Prefer functional components with hooks
- Use React Query for API calls
- Max line length: 100 characters

### SQL/Alembic
- Use lowercase table/column names with underscores
- Always add indexes for foreign keys
- Use JSONB (not JSON) in PostgreSQL
- Add comments for complex migrations

---

## Notes on Conventions

- **Alembic migrations** - Auto-generate with manual review
- **Pydantic validation** - All API inputs validated
- **Model selection:**
  - Haiku = extraction, parsing, requirements
  - Sonnet = generation, cover letters, analysis
- **No 'any' types** - Build proper TypeScript types
- **Check existing deps** - Before installing new packages

---

## Questions to Ask Before...

### Adding a New Dependency
- [ ] Is there an existing solution in the codebase?
- [ ] Is this package actively maintained?
- [ ] What's the bundle size impact? (frontend)
- [ ] Does it have security vulnerabilities? (`yarn audit` / `pip-audit`)

### Running Destructive Operations
- [ ] Do I have a backup?
- [ ] Have I tested on a copy first?
- [ ] Can this be rolled back?
- [ ] Did I ask the user first? (per CLAUDE.md)

**Never without asking:**
- `rm -rf` (destructive file deletion)
- `git push --force` (rewrite history)
- `DROP TABLE` / `DROP DATABASE` (data loss)
- `terraform destroy` (infrastructure deletion)

**Ask before:**
- Creating migrations
- Deleting files/code
- Installing new dependencies
- Editing .env or Terraform configs
- Running `git push`
- Destructive database operations
- `sudo` commands


## Quick Reminders

- ✅ Use Haiku 4.5 for extraction (cheap), Sonnet 4.5 for generation (quality)
- ✅ Cache LLM results aggressively (Redis with 30-day TTL)
- ✅ Test locally before deploying
- ✅ Commit frequently with descriptive messages
- 📍 RemoteOK has JSON API at https://remoteok.com/api (implemented)
- 📍 LinkedIn scraping is harder - save for later (not implemented)
- 📋 Future features documented above: Streaming, User-submitted jobs

## Recent Improvements (Completed)

**Match Filtering & UX:**
- ✅ Match percentage filters are now exclusive (60-69%, 70-84%, 85%+) - no more duplicate jobs across filters
- ✅ Remote/onsite is now a hard filter (not a weighted score) - jobs filtered before matching
- ✅ Skills ARE being saved from job postings (verified working correctly)
- ✅ skill1/skill2 are just LLM prompt placeholders (no database cleanup needed)

**Security & Code Quality:**
- ✅ JWT_SECRET validation with production safeguards
- ✅ Rate limiting on auth endpoints (5 registrations/hour, 10 logins/minute)
- ✅ Timing attack prevention in login
- ✅ CORS hardening with configurable origins
- ✅ Redoc CDN version pinned (v2.1.3)
- ✅ HTML template extracted for maintainability
- ✅ Email allowlist for registration control (with admin API)

---

## Pending Features Checklist

**Pre-Deployment Features:**
- [ ] User-Submitted Jobs - Allow users to paste/add custom job postings
- [ ] Employment Eligibility Filter - Geographic/visa restrictions
- [ ] UI Polish - Loading states, errors, mobile responsiveness
- [ ] Fix Remaining Tests - Get to 100% test coverage (21 backend tests failing)

**Post-Deployment (Nice-to-Have):**
- [ ] Auto-Refresh Matches - Trigger on CV/preferences update
- [ ] Scheduled Scraping - Daily cron job for new jobs
- [ ] Email Notifications - New matches, application reminders
- [ ] Portfolio Write-up - Case study documentation

---

## Future Improvements

### Employment Eligibility Filter

**Problem:** Some jobs are restricted to specific countries/regions (e.g., "US nationals only", "EU work authorization required")

**Proposed Solution:**
1. **LLM Extraction:**
   - Update job requirements extraction prompt to detect eligibility restrictions
   - Extract: `eligible_regions` (["US", "EU", "Worldwide", etc.])
   - Extract: `visa_sponsorship` (true/false)

2. **Database Schema:**
   ```sql
   ALTER TABLE jobs
   ADD COLUMN eligible_regions JSONB DEFAULT '["Worldwide"]',
   ADD COLUMN visa_sponsorship BOOLEAN DEFAULT NULL;
   ```

3. **User Profile:**
   - Add `current_location` or `citizenship` to user preferences
   - Add `needs_visa_sponsorship` boolean

4. **Matching Logic:**
   - Hard filter jobs by eligibility before creating matches
   - Skip jobs where user's location doesn't match `eligible_regions`
   - If user needs sponsorship, filter out jobs with `visa_sponsorship: false`

**Example Prompts:**
```
Job posting text: "Must be authorized to work in the US. No visa sponsorship."
Extracted: {
  "eligible_regions": ["US"],
  "visa_sponsorship": false
}

Job posting text: "Remote position, candidates from EU/US/Canada welcome. Visa sponsorship available."
Extracted: {
  "eligible_regions": ["EU", "US", "Canada"],
  "visa_sponsorship": true
}
```

**Priority:** Medium (after deployment)

---

### Auto-Refresh Matches on Profile Changes

**Problem:** When user updates CV or preferences, matches aren't automatically refreshed

**Solution:**
- Trigger background job to recalculate matches after CV upload
- Trigger background job after preferences update
- Show notification: "Your matches are being refreshed..."

**Priority:** Low (nice-to-have, deferred for now)

---

## ✅ Email Allowlist for Registration (COMPLETED)

**Goal:** Restrict registration to approved emails only for private beta/testing.

**Implementation:**

1. **Database:**
   - New table: `allowed_emails` with columns: id, email, added_by, created_at
   - Migration: `17474fd54e48_add_allowed_emails_table.py`
   - Unique constraint on email field
   - Foreign key to users table

2. **Backend Configuration** (`backend/app/config.py`):
   - `registration_mode`: "open" (default), "allowlist", or "closed"
   - `allowed_emails`: Comma-separated fallback list (e.g., "email1@x.com,email2@y.com")
   - Validator to ensure registration_mode is valid

3. **Registration Endpoint** (`backend/app/routers/auth.py`):
   - Check registration_mode before allowing registration
   - If "closed" → 403 "Registration is currently closed"
   - If "allowlist" → Check DB first, then config fallback (case-insensitive)
   - If "open" → Allow all registrations

4. **Admin API** (`backend/app/routers/admin.py`) - NEW:
   - `POST /api/admin/allowlist` - Add email to allowlist (admin only)
   - `GET /api/admin/allowlist` - List all allowed emails (admin only)
   - `DELETE /api/admin/allowlist/{email}` - Remove email from allowlist (admin only)
   - Simple admin check: user with id=1 is admin (TODO: implement proper role system)

5. **Frontend** (`frontend/src/pages/RegisterPage.tsx`):
   - Already handles 403 errors gracefully
   - Shows friendly message: "Registration is currently invite-only. Your email is not on the allowlist."

**Configuration (.env):**
```bash
REGISTRATION_MODE=open  # or "allowlist" or "closed"
ALLOWED_EMAILS=info@devdenise.com,friend@example.com
```

**Usage:**
- Set `REGISTRATION_MODE=allowlist` to enable invite-only registration
- Use admin API to manage allowed emails dynamically
- Config list serves as fallback if database is empty

**TODO:**
- Add proper role-based admin system (currently user id=1 is admin)
- Add tests for allowlist behavior
- Consider email invitation flow with tokens