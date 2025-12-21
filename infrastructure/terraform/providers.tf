terraform {
  required_version = ">= 1.0"

  cloud {
    organization = "denisenanni"
    workspaces {
      name = "career-agent"
    }
  }

  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "~> 0.4"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 1.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# Railway - manages Postgres, Redis, and Backend deployment
provider "railway" {
  token = var.railway_account_token
}

# Vercel - manages Frontend deployment
provider "vercel" {
  api_token = var.vercel_api_token
  team      = var.vercel_team_id
}

# GitHub - manages Actions secrets and repository configuration
provider "github" {
  token = var.github_token
  owner = split("/", var.github_repo)[0]
}
