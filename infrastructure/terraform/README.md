# Career Agent - Infrastructure as Code

This directory contains Terraform configuration for deploying the Career Agent infrastructure using Railway and Vercel.

## Architecture

- **Railway**: Hosts PostgreSQL, Redis, and FastAPI backend
- **Vercel**: Hosts React frontend

## Prerequisites

1. **Terraform**: Install from https://www.terraform.io/downloads
2. **Railway Account**: Sign up at https://railway.app
3. **Vercel Account**: Sign up at https://vercel.com
4. **Anthropic API Key**: Get from https://console.anthropic.com

## Setup

### 1. Get API Tokens

**Railway**:
- Go to https://railway.app/account/tokens
- Create a new token
- Save it securely

**Vercel**:
- Go to https://vercel.com/account/tokens
- Create a new token with full access
- Save it securely

**Anthropic**:
- Go to https://console.anthropic.com/settings/keys
- Create a new API key
- Save it securely

### 2. Create Variables File

```bash
# Copy the example file
cp terraform.tfvars.example dev.tfvars

# Edit with your values
nano dev.tfvars
```

Fill in the required values:
```hcl
railway_api_token = "your-railway-token"
vercel_api_token  = "your-vercel-token"
anthropic_api_key = "your-anthropic-key"
postgres_password = "generate-secure-password"
jwt_secret        = "generate-with-openssl-rand-base64-32"
```

### 3. Initialize Terraform

```bash
terraform init
```

This downloads the required providers (Railway and Vercel).

### 4. Plan Infrastructure

```bash
terraform plan -var-file=dev.tfvars
```

Review the planned changes to ensure everything looks correct.

### 5. Apply Infrastructure

```bash
terraform apply -var-file=dev.tfvars
```

Type `yes` when prompted to create the infrastructure.

## What Gets Created

### Railway Project

1. **PostgreSQL Service**: Database for storing jobs, users, matches
2. **Redis Service**: Cache for LLM results and session data
3. **Backend Service**: FastAPI application connected to GitHub

### Vercel Project

1. **Frontend Project**: React application deployed from GitHub
2. **Environment Variables**: Configured with backend URL
3. **Custom Domain**: Using Vercel's auto-generated domain

## After Deployment

### View Outputs

```bash
terraform output
```

### Get Environment Variables

```bash
terraform output -raw env_file_content > .env.production
```

### View Deployment Info

```bash
terraform output deployment_info
```

## Railway Configuration

The backend service is configured to:
- Auto-deploy from `main` branch
- Use `/backend` as root directory
- Include all required environment variables
- Connect to PostgreSQL and Redis via Railway's internal network

## Vercel Configuration

The frontend is configured to:
- Auto-deploy from `main` branch
- Use `/frontend` as root directory
- Build with `yarn build`
- Use `dist` as output directory

## Managing Infrastructure

### Update Infrastructure

Make changes to `.tf` files, then:
```bash
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

### Destroy Infrastructure

```bash
terraform destroy -var-file=dev.tfvars
```

**Warning**: This will delete all resources including databases!

### View State

```bash
terraform show
```

## Environments

### Development

```bash
terraform workspace new dev
terraform apply -var-file=dev.tfvars
```

### Production

```bash
terraform workspace new prod
terraform apply -var-file=prod.tfvars
```

## Troubleshooting

### Railway Service Not Deploying

1. Check GitHub repository is connected
2. Verify `/backend` directory has a `Dockerfile` or Railway will auto-detect Python
3. Check Railway dashboard for build logs

### Vercel Build Failing

1. Verify `/frontend` directory structure
2. Check `package.json` has correct build script
3. Review Vercel dashboard for build logs

### Database Connection Issues

1. Verify PostgreSQL service is running in Railway
2. Check environment variables are set correctly
3. Ensure using Railway's internal network URLs (`.railway.internal`)

## Cost Estimate

- **Railway**: $5/month credit (free tier)
- **Vercel**: Free tier
- **Anthropic API**: $10-20/month (usage-based)

Total: **$10-25/month**

## Security Notes

- Never commit `*.tfvars` files
- Store API tokens in secure password manager
- Rotate secrets regularly
- Use different secrets for dev/prod

## Next Steps

After infrastructure is deployed:

1. Connect GitHub repository to Railway backend service
2. Add `Procfile` or `railway.json` to backend if needed
3. Push code to GitHub to trigger deployments
4. Monitor deployments in Railway and Vercel dashboards
