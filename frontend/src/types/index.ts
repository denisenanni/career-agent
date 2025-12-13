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
