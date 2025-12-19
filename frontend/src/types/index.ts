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

// Match types
export interface Match {
  id: number
  job_id: number
  score: number
  status: string
  reasoning: {
    overall_score: number
    skill_score: number
    work_type_score: number
    location_score: number
    salary_score: number
    experience_score: number
    matching_skills: string[]
    missing_skills: string[]
    weights: Record<string, number>
  }
  analysis: string
  created_at: string
  // Job details embedded
  job_title: string
  job_company: string
  job_url: string
  job_location: string
  job_remote_type: string
  job_salary_min: number | null
  job_salary_max: number | null
}

export interface MatchesResponse {
  matches: Match[]
  total: number
  limit: number
  offset: number
}

export interface MatchFilters {
  min_score?: number
  max_score?: number
  status?: string
  limit?: number
  offset?: number
}

export interface RefreshMatchesResponse {
  matches_created: number
  matches_updated: number
  total_jobs_processed: number
}

// Insights types
export interface SkillRecommendation {
  skill: string
  priority: 'high' | 'medium' | 'low'
  reason: string
  frequency: number
  salary_impact: number | null
  learning_effort: 'low' | 'medium' | 'high'
}

export interface SkillAnalysis {
  user_skills: string[]
  skill_gaps: string[]
  recommendations: SkillRecommendation[]
  market_skills: Record<string, {
    count: number
    frequency: number
    avg_salary: number | null
    jobs_with_salary: number
  }>
  jobs_analyzed: number
  analysis_date: string
}

// Generation types
export interface CoverLetterResponse {
  cover_letter: string
  cached: boolean
  generated_at: string
}

export interface CVHighlightsResponse {
  highlights: string[]
  cached: boolean
  generated_at: string
}

export interface RegenerateResponse {
  message: string
  keys_invalidated: number
}
