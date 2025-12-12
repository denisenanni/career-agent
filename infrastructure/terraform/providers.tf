terraform {
  required_version = ">= 1.0"

  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.2"
    }
    upstash = {
      source  = "upstash/upstash"
      version = "~> 1.5"
    }
    fly = {
      source  = "fly-apps/fly"
      version = "~> 0.1"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 1.0"
    }
  }
}

# Neon (PostgreSQL)
provider "neon" {
  api_key = var.neon_api_key
}

# Upstash (Redis)
provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}

# Fly.io
provider "fly" {
  fly_api_token = var.fly_api_token
}

# Vercel
provider "vercel" {
  api_token = var.vercel_api_token
}
