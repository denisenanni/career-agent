# Infrastructure Migration: Fly.io/Neon/Upstash → Railway

## Overview

The Terraform configuration has been migrated from using multiple cloud providers (Fly.io, Neon, Upstash) to a simplified Railway + Vercel stack.

## Changes Made

### 1. Providers Updated

**Before**:
- Neon (PostgreSQL)
- Upstash (Redis)
- Fly.io (Backend)
- Vercel (Frontend)

**After**:
- Railway (PostgreSQL + Redis + Backend)
- Vercel (Frontend)

### 2. File Changes

#### `providers.tf`
- Removed: `neon`, `upstash`, `fly` providers
- Added: `railway` provider
- Kept: `vercel` provider

#### `main.tf`
- Created `railway_project` resource
- Created `railway_service` for PostgreSQL (postgres:16-alpine)
- Created `railway_service` for Redis (redis:7-alpine)
- Created `railway_service` for FastAPI backend
- Configured environment variables for all Railway services
- Updated Vercel project configuration
- Removed Fly.io app and IP resources
- Removed Neon project and database resources
- Removed Upstash Redis database resource

#### `variables.tf`
- Removed: `neon_api_key`, `upstash_email`, `upstash_api_key`, `fly_api_token`, `fly_region`
- Added: `railway_api_token`, `postgres_db`, `postgres_user`, `postgres_password`, `github_branch`
- Kept: `vercel_api_token`, `vercel_team_id`, `anthropic_api_key`, `jwt_secret`, `github_repo`

#### `outputs.tf`
- Updated to output Railway resource IDs and connection strings
- Added `railway_project_id` and `railway_project_name`
- Updated `database_url` to use Railway variables
- Updated `redis_url` to use Railway variables
- Updated `backend_url` to use Railway domain
- Added `deployment_info` summary output
- Updated `env_file_content` for Railway configuration

#### `terraform.tfvars.example`
- Completely rewritten to reflect Railway variables
- Added clear documentation and links for obtaining API tokens
- Organized into logical sections

### 3. New Files Created

#### `README.md`
Comprehensive documentation including:
- Architecture overview
- Prerequisites and setup steps
- Step-by-step deployment instructions
- Troubleshooting guide
- Cost estimates
- Security notes

#### `.gitignore`
Prevents committing sensitive files:
- Terraform state files
- Variable files (*.tfvars)
- Terraform directories
- Environment files

## Migration Benefits

1. **Simplified Stack**: One provider (Railway) instead of three (Fly.io + Neon + Upstash)
2. **Lower Complexity**: Fewer API tokens and accounts to manage
3. **Better Integration**: Railway's internal networking between services
4. **Easier Setup**: Railway's $5/month free credit covers development needs
5. **Consistent Environment**: All backend infrastructure in one place

## Railway Architecture

```
Railway Project: career-agent-dev
├── PostgreSQL Service (postgres:16-alpine)
│   ├── POSTGRES_DB=career_agent
│   ├── POSTGRES_USER=career_agent
│   └── POSTGRES_PASSWORD=<from variables>
├── Redis Service (redis:7-alpine)
└── Backend Service (FastAPI)
    ├── DATABASE_URL → postgres.railway.internal
    ├── REDIS_URL → redis.railway.internal
    ├── ANTHROPIC_API_KEY
    ├── JWT_SECRET
    ├── ENVIRONMENT
    └── LOG_LEVEL
```

## Next Steps for Deployment

1. **Get API Tokens**:
   - Railway: https://railway.app/account/tokens
   - Vercel: https://vercel.com/account/tokens
   - Anthropic: https://console.anthropic.com/settings/keys

2. **Create Variables File**:
   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example dev.tfvars
   # Edit dev.tfvars with your tokens
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Deploy Infrastructure**:
   ```bash
   terraform plan -var-file=dev.tfvars
   terraform apply -var-file=dev.tfvars
   ```

5. **Configure GitHub Repo**:
   - Ensure backend code is in `/backend` directory
   - Ensure frontend code is in `/frontend` directory
   - Railway and Vercel will auto-deploy on push to `main`

## Local Development vs Production

### Local (Docker Compose)
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Backend on `localhost:8000`
- Frontend on `localhost:5173`

### Production (Railway + Vercel)
- PostgreSQL on `<service>.railway.internal:5432`
- Redis on `<service>.railway.internal:6379`
- Backend on `<project>.up.railway.app`
- Frontend on `<project>.vercel.app`

## Cost Comparison

### Before (Fly.io + Neon + Upstash)
- Fly.io: $0-5/month
- Neon: $0 (free tier)
- Upstash: $0 (free tier)
- Anthropic: $10-20/month
- **Total**: $10-25/month

### After (Railway + Vercel)
- Railway: $0-5/month (includes $5 credit)
- Vercel: $0 (free tier)
- Anthropic: $10-20/month
- **Total**: $10-25/month

## Breaking Changes

None for local development - Docker Compose setup remains unchanged.

For production deployments:
- New API tokens required (Railway instead of Fly.io/Neon/Upstash)
- Different connection strings (Railway internal networking)
- Different deployment process (Railway instead of Fly.io CLI)

## Rollback Plan

If needed, the original Terraform files are in git history:
```bash
git log --oneline infrastructure/terraform/
git checkout <commit-hash> infrastructure/terraform/
```

## Testing

Before deploying to production:
1. Test Terraform plan locally
2. Deploy to a Railway dev project first
3. Verify all services start successfully
4. Test backend API endpoints
5. Test frontend can connect to backend
6. Run database migrations
7. Test scraping functionality

## Support

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Terraform Railway Provider: https://registry.terraform.io/providers/terraform-community-providers/railway
