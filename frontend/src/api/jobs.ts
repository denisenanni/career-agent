import type { Job, JobsResponse, JobFilters } from '../types'
import { apiFetch, buildQueryString } from './client'

export async function fetchJobs(filters: JobFilters = {}): Promise<JobsResponse> {
  const queryString = buildQueryString(filters)
  return apiFetch<JobsResponse>(`/api/jobs${queryString}`)
}

export async function fetchJob(id: number): Promise<Job> {
  return apiFetch<Job>(`/api/jobs/${id}`)
}

export async function refreshJobs(): Promise<void> {
  return apiFetch<void>('/api/jobs/refresh', {
    method: 'POST',
    requiresAuth: true,
  })
}
