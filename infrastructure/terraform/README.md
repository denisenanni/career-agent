# Terraform Infrastructure

This directory contains the Terraform configuration for deploying Career Agent to Railway (backend) and Vercel (frontend) with fully automated CI/CD via GitHub Actions.

## Architecture

```
GitHub Actions (CI/CD)
├── Backend: Build Docker → Push to GHCR → Deploy to Railway
└── Frontend: Build → Deploy to Vercel CLI

Railway
├── PostgreSQL (Database)
├── Redis (Cache)
└── Backend (FastAPI - Docker from GHCR)

Vercel
└── Frontend (React + Vite - CLI deployment)
```

## Quick Start

1. **Copy the template**:
   ```bash
   cp dev.tfvars.example dev.tfvars
   ```

2. **Edit `dev.tfvars`** with your API tokens:
   - Railway token: https://railway.app/account/tokens
   - Vercel token: https://vercel.com/account/tokens
   - Anthropic API key: https://console.anthropic.com/

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Review the plan**:
   ```bash
   terraform plan -var-file=dev.tfvars
   ```

5. **Deploy**:
   ```bash
   terraform apply -var-file=dev.tfvars
   ```

6. **Get outputs** (needed for GitHub secrets):
   ```bash
   # Get Vercel Project ID for GitHub secrets
   terraform output vercel_project_id

   # Get all deployment info
   terraform output deployment_info
   ```

7. **Set up GitHub secrets** (see below)

8. **Push to main** to trigger automated deployment

## What Gets Deployed?

### Railway Services
- **PostgreSQL**: Database for application data
- **Redis**: Cache for sessions and API responses
- **Backend**: FastAPI application (Docker container from GHCR)

### Vercel Project
- **Frontend**: React + Vite application
- Configured for deployment via Vercel CLI (no GitHub integration needed)

## GitHub Secrets Setup

After running `terraform apply`, configure these secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value Source | Description |
|------------|-------------|-------------|
| `RAILWAY_TOKEN` | Railway dashboard tokens page | For Railway deployments |
| `VERCEL_TOKEN` | Vercel account tokens page | For Vercel deployments |
| `VERCEL_ORG_ID` | Vercel account settings | Your user/team ID |
| `VERCEL_PROJECT_ID` | `terraform output vercel_project_id` | Project created by Terraform |

## How CI/CD Works

### Backend Workflow (`.github/workflows/backend-deploy.yml`)

Triggers on push to `main` with changes in `backend/`:

1. Builds Docker image from `backend/Dockerfile`
2. Pushes to GitHub Container Registry (GHCR)
3. Deploys to Railway using the Docker image

**No GitHub OAuth required!** Railway pulls from public GHCR.

### Frontend Workflow (`.github/workflows/frontend-deploy.yml`)

Triggers on push to `main` with changes in `frontend/`:

1. Installs dependencies
2. Builds the app
3. Deploys via Vercel CLI

**No GitHub OAuth required!** Vercel CLI handles deployment.

## Environment Variables

All environment variables are automatically configured by Terraform:

### Backend (Railway)
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `ANTHROPIC_API_KEY` - Anthropic API key
- `JWT_SECRET` - JWT signing secret
- `ENVIRONMENT` - dev/prod
- `LOG_LEVEL` - DEBUG/INFO

### Frontend (Vercel)
- `VITE_API_URL` - Backend API URL (auto-set from Railway domain)

## Files

- `main.tf` - Main infrastructure configuration
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output values (URLs, IDs, etc.)
- `providers.tf` - Provider configuration (Railway, Vercel)
- `dev.tfvars` - Your configuration values (gitignored)
- `dev.tfvars.example` - Template for configuration

## Auto-Generated Secrets

If you don't provide values for these, Terraform will generate them:
- `postgres_password` - Random 32-character password
- `jwt_secret` - Random 44-character secret

**Important**: After first apply, extract and save these values:

```bash
terraform output generated_postgres_password
terraform output generated_jwt_secret
```

Then add them to your `dev.tfvars` to persist across destroys.

## Updating Infrastructure

After making changes to `.tf` files:

```bash
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

## Destroying Infrastructure

To tear down everything:

```bash
terraform destroy -var-file=dev.tfvars
```

**Warning**: This deletes all data! Export your database first:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

## Multiple Environments

To deploy separate dev/staging/prod environments:

1. Create environment-specific tfvars:
   ```bash
   cp dev.tfvars.example staging.tfvars
   cp dev.tfvars.example prod.tfvars
   ```

2. Use Terraform workspaces:
   ```bash
   terraform workspace new staging
   terraform apply -var-file=staging.tfvars

   terraform workspace new prod
   terraform apply -var-file=prod.tfvars
   ```

## Troubleshooting

### "Error: No valid credential sources found"
→ Set API tokens in your `dev.tfvars` file

### "Error: resource already exists"
→ Change `project_name` or `environment` in tfvars

### Railway service fails to start
1. Check Railway dashboard for logs
2. Ensure Docker image exists in GHCR and is public
3. Verify GitHub Actions workflow completed successfully

### Vercel deployment fails
1. Check GitHub Actions logs
2. Verify `VERCEL_PROJECT_ID` secret is correct
3. Ensure Vercel project was created by Terraform

### GitHub Actions workflow not triggering
1. Check workflow file syntax (`.github/workflows/*.yml`)
2. Verify GitHub secrets are set correctly
3. Check Actions tab for errors

### Docker image not found
1. Make backend package public in GHCR:
   - Go to https://github.com/denisenanni?tab=packages
   - Click `career-agent/backend`
   - Settings → Change visibility → Public

## State Management

Currently using local state. For teams/production, use remote state:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "career-agent/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Or use Terraform Cloud for free remote state.

## Cost Estimate

- **Railway**: $5/month (Hobby Plan) - includes PostgreSQL, Redis, Backend
- **Vercel**: $0/month (Free tier) - generous limits
- **GitHub Actions**: $0/month (free for public repos, 2000 min/month for private)
- **Anthropic API**: Usage-based

**Total**: ~$5-15/month

## Security Best Practices

1. Never commit `*.tfvars` files
2. Rotate API tokens regularly
3. Use different secrets for dev/prod
4. Enable branch protection on main
5. Review GitHub Actions logs for security issues
6. Keep dependencies updated

## Full Documentation

See [infrastructure/DEPLOYMENT.md](../DEPLOYMENT.md) for complete deployment guide with troubleshooting, monitoring, and advanced configuration.
