# CI/CD Setup - Quick Start

This document provides a quick reference for setting up the fully automated CI/CD pipeline.

## What Was Built

A fully automated deployment pipeline that requires ZERO manual steps after initial setup:

- Push to `main` → Automatic deployment to Railway (backend) and Vercel (frontend)
- No GitHub OAuth required
- No manual builds
- No manual deploys

## Architecture

```
Git Push to Main
     ↓
GitHub Actions
     ├─→ Backend: Docker → GHCR → Railway
     └─→ Frontend: Build → Vercel CLI
```

## One-Time Setup (5 minutes)

### Step 1: Deploy Infrastructure

```bash
cd infrastructure/terraform
cp dev.tfvars.example dev.tfvars
# Edit dev.tfvars with your API tokens
terraform init
terraform apply -var-file=dev.tfvars
```

Get your Vercel Project ID:
```bash
terraform output vercel_project_id
```

### Step 2: Configure GitHub Secrets

Go to: **Settings → Secrets and variables → Actions**

Add 4 secrets:

| Secret | Get From |
|--------|----------|
| `RAILWAY_TOKEN` | https://railway.app/account/tokens |
| `VERCEL_TOKEN` | https://vercel.com/account/tokens |
| `VERCEL_ORG_ID` | https://vercel.com/account (User/Team ID) |
| `VERCEL_PROJECT_ID` | `terraform output vercel_project_id` |

### Step 3: Make Backend Package Public

After first deployment:
1. Go to https://github.com/denisenanni?tab=packages
2. Click `career-agent/backend`
3. Settings → Change visibility → Public

### Step 4: Deploy

```bash
git add .
git commit -m "Setup CI/CD"
git push origin main
```

Watch it deploy:
- GitHub Actions tab → See workflows running
- Railway dashboard → See backend deploying
- Vercel dashboard → See frontend deploying

## Files Created

```
.github/workflows/
├── backend-deploy.yml      # Backend CI/CD
└── frontend-deploy.yml     # Frontend CI/CD

backend/
├── Dockerfile              # Backend container
└── .dockerignore          # Docker ignore rules

infrastructure/
├── DEPLOYMENT.md          # Full deployment guide
└── terraform/
    ├── main.tf            # Updated for Docker
    ├── variables.tf       # Updated for Docker
    ├── README.md          # Updated guide
    └── dev.tfvars.example # Config template
```

## How It Works

### Backend Deployment
1. GitHub Actions detects changes in `backend/`
2. Builds Docker image from `backend/Dockerfile`
3. Pushes to GitHub Container Registry (GHCR)
4. Railway pulls the image and deploys
5. Runs `alembic upgrade head` on startup

### Frontend Deployment
1. GitHub Actions detects changes in `frontend/`
2. Installs dependencies with yarn
3. Builds the app
4. Deploys to Vercel via CLI

## Daily Workflow

Just push to main:

```bash
# Work on backend
vim backend/app/main.py
git add backend/
git commit -m "Add new feature"
git push
# ✅ Automatically deploys to Railway

# Work on frontend
vim frontend/src/App.tsx
git add frontend/
git commit -m "Update UI"
git push
# ✅ Automatically deploys to Vercel

# Work on both
git add .
git commit -m "Full stack update"
git push
# ✅ Both deploy in parallel
```

## Monitoring

### GitHub Actions
- See live builds: GitHub → Actions tab
- Each step shows detailed logs

### Railway
- Dashboard: https://railway.app/dashboard
- View logs, metrics, and deployments

### Vercel
- Dashboard: https://vercel.com/dashboard
- View deployments and analytics

## Troubleshooting

### Backend not deploying?
```bash
# Check GitHub Actions logs
# Verify RAILWAY_TOKEN secret
# Ensure Docker image is public in GHCR
```

### Frontend not deploying?
```bash
# Check GitHub Actions logs
# Verify VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
# Check Vercel dashboard
```

### Workflows not running?
```bash
# Check .github/workflows/*.yml syntax
# Verify GitHub secrets are set
# Check Actions tab for errors
```

## Rollback

### Backend
Railway dashboard → Backend service → Deployments → Click previous → Redeploy

### Frontend
Vercel dashboard → Project → Deployments → Click "..." on previous → Promote to Production

## Documentation

- **Full Guide**: [infrastructure/DEPLOYMENT.md](infrastructure/DEPLOYMENT.md)
- **Terraform**: [infrastructure/terraform/README.md](infrastructure/terraform/README.md)

## Cost

- Railway: $5/month
- Vercel: Free
- GitHub Actions: Free (public repo)

**Total: $5/month**

## Next Steps

1. ✅ Complete setup above
2. ✅ Push to main
3. ✅ Watch it deploy
4. ✅ Never manually deploy again!

Enjoy fully automated deployments!
