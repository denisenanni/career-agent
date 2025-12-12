# =============================================================================
# Career Agent Infrastructure
# =============================================================================

locals {
  app_name = "${var.project_name}-${var.environment}"
}

# =============================================================================
# DATABASE - Neon PostgreSQL
# =============================================================================

resource "neon_project" "main" {
  name      = local.app_name
  region_id = "aws-eu-central-1"  # Frankfurt

  default_endpoint_settings {
    autoscaling_limit_min_cu = 0.25
    autoscaling_limit_max_cu = 1
    suspend_timeout_seconds  = 300  # 5 min idle timeout (free tier friendly)
  }
}

resource "neon_database" "main" {
  project_id = neon_project.main.id
  branch_id  = neon_project.main.default_branch_id
  name       = "career_agent"
  owner_name = neon_project.main.database_user
}

# =============================================================================
# CACHE - Upstash Redis
# =============================================================================

resource "upstash_redis_database" "main" {
  database_name = local.app_name
  region        = "eu-central-1"  # Frankfurt
  tls           = true
  eviction      = true
}

# =============================================================================
# BACKEND - Fly.io
# =============================================================================

resource "fly_app" "backend" {
  name = "${local.app_name}-api"
  org  = "personal"  # Change if you have an org
}

resource "fly_ip" "backend_ipv4" {
  app  = fly_app.backend.name
  type = "v4"
}

resource "fly_ip" "backend_ipv6" {
  app  = fly_app.backend.name
  type = "v6"
}

# Note: Actual deployment done via `fly deploy` CLI
# Terraform sets up the app and IPs

# =============================================================================
# FRONTEND - Vercel
# =============================================================================

resource "vercel_project" "frontend" {
  name      = local.app_name
  framework = "vite"

  git_repository = {
    type = "github"
    repo = var.github_repo
  }

  root_directory = "frontend"

  build_command    = "yarn build"
  output_directory = "dist"

  environment = [
    {
      key    = "VITE_API_URL"
      value  = "https://${fly_app.backend.name}.fly.dev"
      target = ["production", "preview"]
    }
  ]
}

# Production domain (optional - uses vercel subdomain by default)
resource "vercel_project_domain" "frontend" {
  project_id = vercel_project.frontend.id
  domain     = "${local.app_name}.vercel.app"
}
