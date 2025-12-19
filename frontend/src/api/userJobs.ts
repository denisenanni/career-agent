import { getToken } from './auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs/parse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ job_text: jobText }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to parse job text')
  }

  return response.json()
}

export async function createUserJob(job: UserJobCreate): Promise<UserJob> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(job),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create job')
  }

  return response.json()
}

export async function getUserJobs(): Promise<UserJobsResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch jobs')
  }

  return response.json()
}

export async function getUserJob(jobId: number): Promise<UserJob> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs/${jobId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch job')
  }

  return response.json()
}

export async function updateUserJob(jobId: number, updates: Partial<UserJobCreate>): Promise<UserJob> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs/${jobId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update job')
  }

  return response.json()
}

export async function deleteUserJob(jobId: number): Promise<void> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/user-jobs/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete job')
  }
}
