# Career Agent

## Stack
- Backend: Python FastAPI
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL (local dev) / Railway (prod)
- Package manager: yarn

## Workflow
1. Read ROADMAP.md for current phase and deliverables
2. Check in with me before starting - I'll verify the approach
3. Complete tasks for the current phase
4. Mark deliverables as [x] in ROADMAP.md when done
5. Give high-level explanation of each change
6. Keep changes simple and minimal - avoid big rewrites
7. After finishing, ask if I want a walkthrough of the code

## Conventions
- Use Alembic for migrations
- Use pydantic for validation
- Use Haiku for extraction, Sonnet for generation
- Don't use 'any' - build types for everything
- Before installing dependencies, check if one already exists that does the same

## Safety Rules

**Ask before:**
- Running migrations
- Deleting files or directories
- Installing new dependencies
- Modifying .env or terraform files
- Git push, force push, or branch deletion
- Destructive database operations (DROP, TRUNCATE, DELETE without WHERE)
- Running commands with sudo

**Never run without asking:**
- rm -rf
- git push --force
- DROP TABLE / DROP DATABASE
- terraform destroy

## Quality Checks
- Analyze code for security best practices
- Confirm no sensitive data exposed in frontend
- Check for exploitable vulnerabilities