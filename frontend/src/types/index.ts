export interface Job {
  id: number
  source: string
  source_id: string
  url: string
  title: string
  company: string
  description: string
  salary_min: number | null
  salary_max: number | null
  salary_currency: string
  location: string
  remote_type: string
  job_type: string
  tags: string[]
  posted_at: string | null
  scraped_at: string | null
}

export interface JobsResponse {
  jobs: Job[]
  total: number
  limit: number
  offset: number
}

export interface JobFilters {
  source?: string
  job_type?: string
  remote_type?: string
  min_salary?: number
  search?: string
  limit?: number
  offset?: number
}

// Auth types
export interface User {
  id: number
  email: string
  full_name: string | null
  bio: string | null
  skills: string[]
  experience_years: number | null
  preferences: Record<string, any>
  cv_filename: string | null
  cv_uploaded_at: string | null
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

// Profile types
export interface ProfileUpdate {
  full_name?: string
  bio?: string
  skills?: string[]
  experience_years?: number
  preferences?: Record<string, any>
}

export interface CVUploadResponse {
  filename: string
  file_size: number
  content_type: string
  cv_text_length: number
  uploaded_at: string
  message: string
}

export interface ParsedCV {
  name: string
  email: string | null
  phone: string | null
  summary: string
  skills: string[]
  experience: Array<{
    company: string
    title: string
    start_date: string | null
    end_date: string | null
    description: string
  }>
  education: Array<{
    institution: string
    degree: string
    field: string | null
    end_date: string | null
  }>
  years_of_experience: number
}
