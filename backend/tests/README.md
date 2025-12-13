# Backend Tests

Comprehensive test suite for the Career Agent backend, focusing on the scraper service and data validation.

## Test Structure

```
tests/
├── unit/                      # Unit tests (work with SQLite)
│   └── test_job_schema.py    # JobScrapedData validation & HTML sanitization
├── integration/               # Integration tests (require PostgreSQL)
│   └── test_scraper_service.py # ScraperService database operations
├── conftest.py               # Pytest fixtures and configuration
└── README.md                 # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests (uses SQLite for unit tests, PostgreSQL for integration)
TEST_DATABASE_URL="postgresql://career_agent:career_agent_dev@localhost:5432/career_agent" \
  .venv/bin/python -m pytest tests/

# Run only unit tests (no database needed)
.venv/bin/python -m pytest tests/unit/ -v

# Run only integration tests (requires PostgreSQL)
TEST_DATABASE_URL="postgresql://career_agent:career_agent_dev@localhost:5432/career_agent" \
  .venv/bin/python -m pytest tests/integration/ -v
```

### With Docker PostgreSQL

```bash
# Start PostgreSQL
docker-compose up -d

# Run all tests
TEST_DATABASE_URL="postgresql://career_agent:career_agent_dev@localhost:5432/career_agent" \
  .venv/bin/python -m pytest tests/ -v
```

### Coverage Report

```bash
# Generate coverage report
TEST_DATABASE_URL="postgresql://career_agent:career_agent_dev@localhost:5432/career_agent" \
  .venv/bin/python -m pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Coverage

### Unit Tests (23 tests)

**JobScrapedData Validation (14 tests)**
- ✅ Valid job data validation
- ✅ Required fields validation (source_id, url, title, company, description)
- ✅ URL format validation
- ✅ Field length constraints
- ✅ Salary range validation
- ✅ Tags validation (empty strings, whitespace, max length)
- ✅ Whitespace stripping

**HTML Sanitization (9 tests)**
- ✅ XSS prevention via HTML entity escaping
- ✅ Recursive sanitization for dicts/lists
- ✅ Performance optimization (skip technical fields, max depth, large lists)
- ✅ Integration with JobScrapedData schema

### Integration Tests (23 tests)

**ScraperService.save_jobs (10 tests)**
- ✅ Saving new jobs
- ✅ Updating existing jobs
- ✅ Mixed new and updated jobs
- ✅ Validation error handling
- ✅ Timestamp management (created_at, updated_at, scraped_at)
- ✅ Batch commit behavior (250 jobs per batch)
- ✅ Source isolation

**ScraperService Helper Methods (7 tests)**
- ✅ get_job_by_source_id
- ✅ get_recent_jobs (filtering, ordering, limits)
- ✅ Source-specific queries

**ScrapeLog Management (4 tests)**
- ✅ Creating scrape logs
- ✅ Updating scrape logs (success/failure)
- ✅ Error handling

**Performance Tests (2 tests)**
- ✅ N+1 query prevention via batch queries
- ✅ HTML sanitization applied correctly

## Test Fixtures

### db_session
- Creates fresh test database for each test
- Uses PostgreSQL if `TEST_DATABASE_URL` is set, otherwise SQLite
- Automatic cleanup after each test

### sample_job_data
- Valid job data dictionary for testing

### sample_jobs_batch
- Batch of 5 job records for bulk testing

### existing_job
- Pre-created job in database for update tests

## Test Configuration

Configuration in `pytest.ini`:
- Coverage reporting enabled
- HTML coverage report generated
- Strict markers mode
- Short traceback format

## Continuous Integration

For CI/CD, use:

```bash
# Install dependencies
pip install -r requirements.txt

# Start database
docker-compose up -d

# Wait for database
sleep 5

# Run tests
TEST_DATABASE_URL="postgresql://career_agent:career_agent_dev@localhost:5432/career_agent" \
  pytest tests/ -v --cov=app --cov-fail-under=80
```

## Performance Optimizations Tested

All performance optimizations are validated:
1. ✅ Regex pattern pre-compilation
2. ✅ HTML sanitization with depth/list limits
3. ✅ Batch database commits (250 per batch)
4. ✅ N+1 query prevention
5. ✅ Logging performance guards

## Security Tests

XSS prevention validated:
- ✅ HTML entities properly escaped
- ✅ Recursive sanitization in raw_data
- ✅ No script injection possible
