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

# Neon
variable "neon_api_key" {
  description = "Neon API key"
  type        = string
  sensitive   = true
}

# Upstash
variable "upstash_email" {
  description = "Upstash account email"
  type        = string
}

variable "upstash_api_key" {
  description = "Upstash API key"
  type        = string
  sensitive   = true
}

# Fly.io
variable "fly_api_token" {
  description = "Fly.io API token"
  type        = string
  sensitive   = true
}

variable "fly_region" {
  description = "Fly.io region"
  type        = string
  default     = "fra"  # Frankfurt - closest to Italy
}

# Vercel
variable "vercel_api_token" {
  description = "Vercel API token"
  type        = string
  sensitive   = true
}

variable "vercel_team_id" {
  description = "Vercel team ID (optional, for team accounts)"
  type        = string
  default     = null
}

# App
variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret for auth"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository for Vercel deployment"
  type        = string
  default     = "denisenanni/career-agent"
}
