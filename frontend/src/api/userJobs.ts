import { apiFetch } from './client'

export interface UserJob {
  id: number
  user_id: number
  title: string
  company: string | null
  description: string
  url: string | null
  source: string
  tags: string[]
  salary_min: number | null
  salary_max: number | null
  salary_currency: string
  location: string | null
  remote_type: string | null
  job_type: string | null
  created_at: string
  updated_at: string
}

export interface UserJobCreate {
  title: string
  company?: string | null
  description: string
  url?: string | null
  location?: string | null
  remote_type?: string | null
  job_type?: string | null
  salary_min?: number | null
  salary_max?: number | null
  salary_currency?: string
  tags?: string[]
}

export interface UserJobsResponse {
  jobs: UserJob[]
  total: number
}

export async function parseJobText(jobText: string): Promise<UserJobCreate> {
  return apiFetch<UserJobCreate>('/api/user-jobs/parse', {
    method: 'POST',
    requiresAuth: true,
    body: JSON.stringify({ job_text: jobText }),
  })
}

export async function createUserJob(job: UserJobCreate): Promise<UserJob> {
  return apiFetch<UserJob>('/api/user-jobs', {
    method: 'POST',
    requiresAuth: true,
    body: JSON.stringify(job),
  })
}

export async function getUserJobs(): Promise<UserJobsResponse> {
  return apiFetch<UserJobsResponse>('/api/user-jobs', { requiresAuth: true })
}

export async function getUserJob(jobId: number): Promise<UserJob> {
  return apiFetch<UserJob>(`/api/user-jobs/${jobId}`, { requiresAuth: true })
}

export async function updateUserJob(jobId: number, updates: Partial<UserJobCreate>): Promise<UserJob> {
  return apiFetch<UserJob>(`/api/user-jobs/${jobId}`, {
    method: 'PUT',
    requiresAuth: true,
    body: JSON.stringify(updates),
  })
}

export async function deleteUserJob(jobId: number): Promise<void> {
  return apiFetch<void>(`/api/user-jobs/${jobId}`, {
    method: 'DELETE',
    requiresAuth: true,
  })
}
