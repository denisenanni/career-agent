variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "career-agent"
}

# =============================================================================
# RAILWAY
# =============================================================================

variable "railway_api_token" {
  description = "Railway API token (get from https://railway.app/account/tokens)"
  type        = string
  sensitive   = true
}

# Database credentials
variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "career_agent"
}

variable "postgres_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "career_agent"
}

variable "postgres_password" {
  description = "PostgreSQL password (auto-generated if not provided)"
  type        = string
  sensitive   = true
  default     = null
}

# =============================================================================
# VERCEL
# =============================================================================

variable "vercel_api_token" {
  description = "Vercel API token (get from https://vercel.com/account/tokens)"
  type        = string
  sensitive   = true
}

variable "vercel_team_id" {
  description = "Vercel team ID (optional, for team accounts)"
  type        = string
  default     = null
}

# =============================================================================
# APPLICATION
# =============================================================================

variable "anthropic_api_key" {
  description = "Anthropic API key (get from https://console.anthropic.com/)"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret for authentication (auto-generated if not provided)"
  type        = string
  sensitive   = true
  default     = null
}

variable "allowed_emails" {
  description = "Comma-separated list of allowed email addresses for registration"
  type        = string
  default     = ""
}

variable "frontend_url" {
  description = "Frontend URL for CORS (get from Vercel after deployment)"
  type        = string
  default     = "*"  # Allow all origins initially, update after Vercel deployment
}

# =============================================================================
# DOCKER IMAGES
# =============================================================================

variable "backend_docker_image" {
  description = "Backend Docker image from GHCR (deployed by GitHub Actions)"
  type        = string
  default     = "ghcr.io/denisenanni/career-agent/backend:latest"
}

# =============================================================================
# GITHUB
# =============================================================================

variable "github_repo" {
  description = "GitHub repository (format: owner/repo)"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch for deployments"
  type        = string
  default     = "main"
}

variable "github_token" {
  description = "GitHub personal access token for managing Actions secrets"
  type        = string
  sensitive   = true
}
