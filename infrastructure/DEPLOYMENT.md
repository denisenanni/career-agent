# Automated Deployment Guide

This guide explains how to set up fully automated CI/CD deployment for the Career Agent application using GitHub Actions, Railway, and Vercel.

## Overview

The deployment is fully automated:
- **Backend**: GitHub Actions builds a Docker image, pushes to GitHub Container Registry (GHCR), and deploys to Railway
- **Frontend**: GitHub Actions builds and deploys to Vercel via CLI
- **Infrastructure**: Terraform manages all cloud resources
- **Triggers**: Every push to `main` branch automatically deploys changes

## Architecture

```
┌─────────────────┐
│  Git Push       │
│  to main        │
└────────┬────────┘
         │
         ├───────────────────────────────────┐
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ Backend Workflow │              │Frontend Workflow │
│                  │              │                  │
│ 1. Build Docker  │              │ 1. Install deps  │
│ 2. Push to GHCR  │              │ 2. Build app     │
│ 3. Deploy Railway│              │ 3. Deploy Vercel │
└──────────────────┘              └──────────────────┘
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│   Railway        │              │    Vercel        │
│   (Backend API)  │◄────────────►│   (Frontend)     │
└──────────────────┘              └──────────────────┘
```

## Prerequisites

1. **GitHub Account** with admin access to the repository
2. **Railway Account** at https://railway.app
3. **Vercel Account** at https://vercel.com
4. **Anthropic API Key** from https://console.anthropic.com

## One-Time Setup

### Step 1: Get API Tokens

#### Railway Token
1. Go to https://railway.app/account/tokens
2. Click "Create Token"
3. Name it "GitHub Actions"
4. Copy the token - you'll need it for GitHub secrets

#### Vercel Token
1. Go to https://vercel.com/account/tokens
2. Click "Create Token"
3. Name it "GitHub Actions"
4. Set scope to "Full Account"
5. Copy the token - you'll need it for GitHub secrets

#### Vercel Organization ID
1. Go to https://vercel.com/account
2. Click on "Settings"
3. Under "General", copy your "User ID" or "Team ID"
4. This is your `VERCEL_ORG_ID`

### Step 2: Deploy Infrastructure with Terraform

1. Navigate to the terraform directory:
   ```bash
   cd infrastructure/terraform
   ```

2. Create a `dev.tfvars` file (or update existing):
   ```hcl
   # Required
   railway_api_token = "your-railway-token"
   vercel_api_token  = "your-vercel-token"
   anthropic_api_key = "your-anthropic-key"

   # Optional (will be auto-generated if not provided)
   postgres_password = null
   jwt_secret        = null
   ```

3. Initialize and deploy:
   ```bash
   terraform init
   terraform apply -var-file=dev.tfvars
   ```

4. **Important**: After `terraform apply` completes, save the output:
   ```bash
   # Get the Vercel Project ID
   terraform output vercel_project_id

   # Get all deployment info
   terraform output deployment_info
   ```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository settings: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add the following secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `RAILWAY_TOKEN` | Railway API token | Step 1 - Railway Token |
| `VERCEL_TOKEN` | Vercel API token | Step 1 - Vercel Token |
| `VERCEL_ORG_ID` | Your Vercel user/team ID | Step 1 - Vercel Organization ID |
| `VERCEL_PROJECT_ID` | Project ID from Terraform | Step 2 - `terraform output vercel_project_id` |

### Step 4: Enable GitHub Packages

The backend workflow pushes Docker images to GitHub Container Registry (GHCR). This is automatically enabled, but you need to make the package public:

1. After the first deployment, go to: `https://github.com/denisenanni?tab=packages`
2. Click on `career-agent/backend`
3. Click `Package settings`
4. Scroll to "Danger Zone"
5. Click "Change visibility" → "Public"

This allows Railway to pull the image without authentication.

### Step 5: Trigger First Deployment

Push a commit to main or manually trigger workflows:

```bash
git add .
git commit -m "Setup automated CI/CD"
git push origin main
```

Or trigger manually:
1. Go to `Actions` tab in GitHub
2. Select `Backend - Build & Deploy` or `Frontend - Build & Deploy`
3. Click `Run workflow` → `Run workflow`

## Deployment Workflows

### Backend Workflow
**File**: `.github/workflows/backend-deploy.yml`

**Triggers on**:
- Push to `main` with changes in `backend/` directory
- Manual trigger via GitHub Actions UI

**Steps**:
1. Checkout code
2. Login to GitHub Container Registry
3. Build Docker image from `backend/Dockerfile`
4. Push image to `ghcr.io/denisenanni/career-agent/backend:latest`
5. Install Railway CLI
6. Deploy to Railway using the Docker image

### Frontend Workflow
**File**: `.github/workflows/frontend-deploy.yml`

**Triggers on**:
- Push to `main` with changes in `frontend/` directory
- Manual trigger via GitHub Actions UI

**Steps**:
1. Checkout code
2. Setup Node.js and install dependencies
3. Install Vercel CLI
4. Pull Vercel environment
5. Build the frontend
6. Deploy to Vercel production

## Environment Variables

All environment variables are managed by Terraform:

### Backend (Railway)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ANTHROPIC_API_KEY` - Anthropic API key
- `JWT_SECRET` - JWT signing secret
- `ENVIRONMENT` - Environment name (dev/prod)
- `LOG_LEVEL` - Logging level

### Frontend (Vercel)
- `VITE_API_URL` - Backend API URL (auto-set from Railway domain)

## Monitoring Deployments

### GitHub Actions
1. Go to the `Actions` tab in your repository
2. Click on a workflow run to see logs
3. Each step shows detailed output

### Railway
1. Go to https://railway.app/dashboard
2. Select your project
3. Click on the `backend` service
4. View "Deployments" tab for history
5. View "Logs" tab for runtime logs

### Vercel
1. Go to https://vercel.com/dashboard
2. Select your project
3. Click "Deployments" to see history
4. Click a deployment to see build logs

## Troubleshooting

### Backend deployment fails
- Check GitHub Actions logs for build errors
- Verify `RAILWAY_TOKEN` secret is correct
- Ensure Docker image is public in GHCR
- Check Railway dashboard for service logs

### Frontend deployment fails
- Check GitHub Actions logs for build errors
- Verify `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` secrets
- Ensure Vercel project exists (created by Terraform)

### Database migration issues
- Railway runs `alembic upgrade head` on container startup
- Check Railway logs for migration errors
- SSH into Railway container: `railway run bash`

### Environment variables not updating
- Backend: Update via Terraform, then redeploy
- Frontend: Update via Terraform, Vercel CLI pulls automatically

## Making Changes

### Update Backend Code
```bash
# Make changes in backend/
git add backend/
git commit -m "Update backend feature"
git push origin main
```
→ GitHub Actions automatically builds and deploys

### Update Frontend Code
```bash
# Make changes in frontend/
git add frontend/
git commit -m "Update frontend UI"
git push origin main
```
→ GitHub Actions automatically builds and deploys

### Update Infrastructure
```bash
cd infrastructure/terraform
# Edit .tf files
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```
→ Infrastructure updated, may need to redeploy services

## Rollback

### Backend
1. Go to Railway dashboard
2. Select backend service
3. Click "Deployments"
4. Click on a previous deployment
5. Click "Redeploy"

### Frontend
1. Go to Vercel dashboard
2. Select project
3. Click "Deployments"
4. Find previous deployment
5. Click "..." → "Promote to Production"

Or via CLI:
```bash
vercel rollback
```

## Cost Estimates

### Railway (Backend)
- **Hobby Plan**: $5/month
- Includes PostgreSQL, Redis, and backend service
- Up to $5 of usage included

### Vercel (Frontend)
- **Free Tier**: $0/month
- Generous limits for hobby projects
- Upgrade to Pro ($20/month) for production

### GitHub Actions
- **Free for public repos**: Unlimited minutes
- **Private repos**: 2,000 minutes/month free

## Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets and Terraform variables
2. **Rotate tokens** - Periodically regenerate API tokens
3. **Use environment-specific configs** - Separate dev/staging/prod
4. **Enable branch protection** - Require PR reviews for main branch
5. **Monitor logs** - Regularly check Railway and Vercel logs
6. **Use semantic versioning** - Tag Docker images with version numbers

## Advanced Configuration

### Multiple Environments

Create separate tfvars files:
```bash
infrastructure/terraform/
├── dev.tfvars
├── staging.tfvars
└── prod.tfvars
```

Deploy each:
```bash
terraform workspace new staging
terraform apply -var-file=staging.tfvars
```

### Custom Domains

#### Backend (Railway)
1. Add domain in Railway dashboard
2. Update DNS records
3. Railway automatically provisions SSL

#### Frontend (Vercel)
1. Add domain in Vercel dashboard
2. Update DNS records
3. Vercel automatically provisions SSL

### Database Backups

Railway automatically backs up PostgreSQL. To create manual backups:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

## Support

- **Railway**: https://railway.app/help
- **Vercel**: https://vercel.com/support
- **GitHub Actions**: https://docs.github.com/actions
- **Terraform**: https://www.terraform.io/docs
