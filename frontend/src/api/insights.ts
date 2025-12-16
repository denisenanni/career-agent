import type { SkillAnalysis } from '../types'

const API_URL = import.meta.env.VITE_API_URL || ''

export async function fetchSkillInsights(refresh = false): Promise<SkillAnalysis> {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('Not authenticated')
  }

  const params = new URLSearchParams()
  if (refresh) params.append('refresh', 'true')

  const response = await fetch(`${API_URL}/api/insights/skills?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 400) {
      const error = await response.json()
      throw new Error(error.detail || 'Bad request')
    }
    throw new Error('Failed to fetch skill insights')
  }

  return response.json()
}

export async function refreshSkillInsights(): Promise<SkillAnalysis> {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/insights/skills/refresh`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 400) {
      const error = await response.json()
      throw new Error(error.detail || 'Bad request')
    }
    throw new Error('Failed to refresh skill insights')
  }

  return response.json()
}
