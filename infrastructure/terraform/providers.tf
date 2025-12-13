terraform {
  required_version = ">= 1.0"

  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "~> 0.4"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 1.0"
    }
  }
}

# Railway - manages Postgres, Redis, and Backend deployment
provider "railway" {
  token = var.railway_api_token
}

# Vercel - manages Frontend deployment
provider "vercel" {
  api_token = var.vercel_api_token
  team      = var.vercel_team_id
}
