# =============================================================================
# Career Agent Infrastructure - Railway + Vercel
# =============================================================================

# =============================================================================
# AUTO-GENERATED SECRETS (if not provided)
# =============================================================================

resource "random_password" "postgres_password" {
  count   = var.postgres_password == null ? 1 : 0
  length  = 32
  special = false  # Railway-safe characters
}

resource "random_password" "jwt_secret" {
  count   = var.jwt_secret == null ? 1 : 0
  length  = 44
  special = true
}

resource "random_password" "scraper_api_key" {
  count   = var.scraper_api_key == null ? 1 : 0
  length  = 48
  special = false  # URL-safe characters only
}

locals {
  app_name          = "${var.project_name}-${var.environment}"
  postgres_password = var.postgres_password != null ? var.postgres_password : random_password.postgres_password[0].result
  jwt_secret        = var.jwt_secret != null ? var.jwt_secret : random_password.jwt_secret[0].result
  scraper_api_key   = var.scraper_api_key != null ? var.scraper_api_key : random_password.scraper_api_key[0].result
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
  project_id   = railway_project.main.id
  name         = "postgres"
  source_image = "postgres:16-alpine"
}

# PostgreSQL environment variables
resource "railway_variable" "postgres_db" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.postgres.id
  name           = "POSTGRES_DB"
  value          = "career_agent"
}

resource "railway_variable" "postgres_user" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.postgres.id
  name           = "POSTGRES_USER"
  value          = "career_agent"
}

resource "railway_variable" "postgres_password" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.postgres.id
  name           = "POSTGRES_PASSWORD"
  value          = local.postgres_password
}

# =============================================================================
# CACHE - Railway Redis
# =============================================================================

resource "railway_service" "redis" {
  project_id   = railway_project.main.id
  name         = "redis"
  source_image = "redis:7-alpine"
}

# =============================================================================
# BACKEND - Railway FastAPI Service
# =============================================================================

resource "railway_service" "backend" {
  project_id   = railway_project.main.id
  name         = "backend"
  source_image = var.backend_docker_image
}

# Backend public domain
resource "railway_service_domain" "backend" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  subdomain      = "${local.app_name}-api"
}

# Backend environment variables
resource "railway_variable" "backend_database_url" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "DATABASE_URL"
  value          = "postgresql://${var.postgres_user}:${local.postgres_password}@${railway_service.postgres.name}.railway.internal:5432/${var.postgres_db}"
}

resource "railway_variable" "backend_redis_url" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "REDIS_URL"
  value          = "redis://${railway_service.redis.name}.railway.internal:6379"
}

resource "railway_variable" "backend_anthropic_key" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "ANTHROPIC_API_KEY"
  value          = var.anthropic_api_key
}

resource "railway_variable" "backend_jwt_secret" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "JWT_SECRET"
  value          = local.jwt_secret
}

resource "railway_variable" "backend_environment" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "ENVIRONMENT"
  value          = var.environment
}

resource "railway_variable" "backend_log_level" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "LOG_LEVEL"
  value          = var.environment == "production" ? "INFO" : "DEBUG"
}

resource "railway_variable" "backend_port" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "PORT"
  value          = "8080"
}

resource "railway_variable" "backend_cors_origins" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "CORS_ORIGINS"
  value          = "https://${local.app_name}.vercel.app"
}

resource "railway_variable" "backend_registration_mode" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "REGISTRATION_MODE"
  value          = "allowlist"
}

resource "railway_variable" "backend_allowed_emails" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "ALLOWED_EMAILS"
  value          = var.allowed_emails
}

resource "railway_variable" "backend_scraper_api_key" {
  environment_id = railway_project.main.default_environment.id
  service_id     = railway_service.backend.id
  name           = "SCRAPER_API_KEY"
  value          = local.scraper_api_key
}

# =============================================================================
# FRONTEND - Vercel
# =============================================================================

resource "vercel_project" "frontend" {
  name      = local.app_name
  framework = "vite"

  # GitHub Actions handles deployment via Vercel CLI
  # No git_repository block needed - avoids OAuth requirement

  build_command    = "yarn build"
  output_directory = "dist"
}

# Frontend environment variables
resource "vercel_project_environment_variable" "api_url" {
  project_id = vercel_project.frontend.id
  key        = "VITE_API_URL"
  value      = "https://${railway_service_domain.backend.domain}"
  target     = ["production", "preview"]
}

# Production domain - Vercel auto-assigns one
# Removed because domain was already taken by another project
# Vercel will provide an auto-generated domain

# =============================================================================
# GITHUB ACTIONS SECRETS
# =============================================================================

# Railway project token for backend deployment (scoped to project)
resource "github_actions_secret" "railway_token" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "RAILWAY_TOKEN"
  plaintext_value = var.railway_project_token
}

# Vercel API token for frontend deployment
resource "github_actions_secret" "vercel_token" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "VERCEL_TOKEN"
  plaintext_value = var.vercel_api_token
}

# Vercel Organization ID (for team accounts)
resource "github_actions_secret" "vercel_org_id" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "VERCEL_ORG_ID"
  plaintext_value = var.vercel_org_id
}

# Vercel Project ID for deployment targeting
resource "github_actions_secret" "vercel_project_id" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "VERCEL_PROJECT_ID"
  plaintext_value = vercel_project.frontend.id
}

# Railway Project ID for linking
resource "github_actions_secret" "railway_project_id" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "RAILWAY_PROJECT_ID"
  plaintext_value = railway_project.main.id
}

# =============================================================================
# SCHEDULED JOBS SECRETS
# =============================================================================

# API URL for scheduled scraping job
resource "github_actions_secret" "api_url" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "API_URL"
  plaintext_value = "https://${railway_service_domain.backend.domain}"
}

# Scraper API key for scheduled scraping job
resource "github_actions_secret" "scraper_api_key" {
  repository      = split("/", var.github_repo)[1]
  secret_name     = "SCRAPER_API_KEY"
  plaintext_value = local.scraper_api_key
}
