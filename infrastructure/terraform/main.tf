# =============================================================================
# Career Agent Infrastructure - Railway + Vercel
# =============================================================================

locals {
  app_name = "${var.project_name}-${var.environment}"
}

# =============================================================================
# RAILWAY PROJECT
# =============================================================================

resource "railway_project" "main" {
  name = local.app_name
}

# =============================================================================
# DATABASE - Railway PostgreSQL
# =============================================================================

resource "railway_service" "postgres" {
  project_id = railway_project.main.id
  name       = "postgres"

  # Use Railway's PostgreSQL template
  source = {
    image = "postgres:16-alpine"
  }
}

# PostgreSQL environment variables
resource "railway_variable" "postgres_db" {
  project_id = railway_project.main.id
  service_id = railway_service.postgres.id
  name       = "POSTGRES_DB"
  value      = "career_agent"
}

resource "railway_variable" "postgres_user" {
  project_id = railway_project.main.id
  service_id = railway_service.postgres.id
  name       = "POSTGRES_USER"
  value      = "career_agent"
}

resource "railway_variable" "postgres_password" {
  project_id = railway_project.main.id
  service_id = railway_service.postgres.id
  name       = "POSTGRES_PASSWORD"
  value      = var.postgres_password
}

# =============================================================================
# CACHE - Railway Redis
# =============================================================================

resource "railway_service" "redis" {
  project_id = railway_project.main.id
  name       = "redis"

  # Use Railway's Redis template
  source = {
    image = "redis:7-alpine"
  }
}

# =============================================================================
# BACKEND - Railway FastAPI Service
# =============================================================================

resource "railway_service" "backend" {
  project_id = railway_project.main.id
  name       = "backend"

  # Connect to GitHub repository
  source = {
    repo           = var.github_repo
    branch         = var.github_branch
    root_directory = "/backend"
  }
}

# Backend environment variables
resource "railway_variable" "backend_database_url" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "DATABASE_URL"
  value      = "postgresql://${var.postgres_user}:${var.postgres_password}@${railway_service.postgres.name}.railway.internal:5432/${var.postgres_db}"
}

resource "railway_variable" "backend_redis_url" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "REDIS_URL"
  value      = "redis://${railway_service.redis.name}.railway.internal:6379"
}

resource "railway_variable" "backend_anthropic_key" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "ANTHROPIC_API_KEY"
  value      = var.anthropic_api_key
}

resource "railway_variable" "backend_jwt_secret" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "JWT_SECRET"
  value      = var.jwt_secret
}

resource "railway_variable" "backend_environment" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "ENVIRONMENT"
  value      = var.environment
}

resource "railway_variable" "backend_log_level" {
  project_id = railway_project.main.id
  service_id = railway_service.backend.id
  name       = "LOG_LEVEL"
  value      = var.environment == "production" ? "INFO" : "DEBUG"
}

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
}

# Frontend environment variables
resource "vercel_project_environment_variable" "api_url" {
  project_id = vercel_project.frontend.id
  key        = "VITE_API_URL"
  value      = railway_service.backend.domain
  target     = ["production", "preview"]
}

# Production domain (uses Vercel's auto-generated domain)
resource "vercel_project_domain" "frontend" {
  project_id = vercel_project.frontend.id
  domain     = "${local.app_name}.vercel.app"
}
