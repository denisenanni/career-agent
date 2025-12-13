import type { Job, JobsResponse, JobFilters } from '../types'

const API_URL = import.meta.env.VITE_API_URL || ''

export async function fetchJobs(filters: JobFilters = {}): Promise<JobsResponse> {
  const params = new URLSearchParams()

  if (filters.source) params.append('source', filters.source)
  if (filters.job_type) params.append('job_type', filters.job_type)
  if (filters.remote_type) params.append('remote_type', filters.remote_type)
  if (filters.min_salary) params.append('min_salary', filters.min_salary.toString())
  if (filters.search) params.append('search', filters.search)
  if (filters.limit) params.append('limit', filters.limit.toString())
  if (filters.offset) params.append('offset', filters.offset.toString())

  const response = await fetch(`${API_URL}/api/jobs?${params.toString()}`)

  if (!response.ok) {
    throw new Error('Failed to fetch jobs')
  }

  return response.json()
}

export async function fetchJob(id: number): Promise<Job> {
  const response = await fetch(`${API_URL}/api/jobs/${id}`)

  if (!response.ok) {
    throw new Error('Failed to fetch job')
  }

  return response.json()
}

export async function refreshJobs(): Promise<void> {
  const response = await fetch(`${API_URL}/api/jobs/refresh`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error('Failed to trigger job refresh')
  }
}
