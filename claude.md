# Career Agent

## Stack
- Backend: Python FastAPI
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL (Railway)

## Safety Rules
- Ask before running migrations
- Ask before deleting files
- Ask before modifying terraform

## Conventions
- Use Alembic for migrations
- Use pydantic for validation
- Haiku for extraction, Sonnet for generation

## Safety Rules

Before running any of these, ask for confirmation:
- Deleting files or directories
- Running migrations on production
- Installing new dependencies
- Modifying .env files
- Git push, force push, or branch deletion
- Any destructive database operations (DROP, TRUNCATE, DELETE without WHERE)
- Running commands with sudo
- Modifying infrastructure/terraform files

Never run without asking:
- rm -rf
- git push --force
- DROP TABLE / DROP DATABASE
- terraform destroy