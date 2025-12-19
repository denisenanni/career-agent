import type { SkillAnalysis } from '../types'
import { apiFetch, buildQueryString } from './client'

export async function fetchSkillInsights(refresh = false): Promise<SkillAnalysis> {
  const queryString = buildQueryString({ refresh: refresh ? 'true' : undefined })
  return apiFetch<SkillAnalysis>(`/api/insights/skills${queryString}`, { requiresAuth: true })
}

export async function refreshSkillInsights(): Promise<SkillAnalysis> {
  return apiFetch<SkillAnalysis>('/api/insights/skills/refresh', {
    method: 'POST',
    requiresAuth: true,
  })
}
