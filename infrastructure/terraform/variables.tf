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
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
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
  description = "JWT secret for authentication (generate with: openssl rand -base64 32)"
  type        = string
  sensitive   = true
}

# =============================================================================
# GIT REPOSITORY
# =============================================================================

variable "github_repo" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = "denisenanni/career-agent"
}

variable "github_branch" {
  description = "GitHub branch to deploy from"
  type        = string
  default     = "main"
}
