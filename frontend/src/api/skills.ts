import { apiFetch, buildQueryString } from './client'

export interface PopularSkillsResponse {
  skills: string[]
  total: number
}

export interface AddCustomSkillResponse {
  skill: string
  created: boolean
  usage_count: number
}

export async function getPopularSkills(limit: number = 200): Promise<PopularSkillsResponse> {
  const queryString = buildQueryString({ limit })
  return apiFetch<PopularSkillsResponse>(`/api/skills/popular${queryString}`)
}

export async function addCustomSkill(skill: string): Promise<AddCustomSkillResponse> {
  return apiFetch<AddCustomSkillResponse>('/api/skills/custom', {
    method: 'POST',
    body: JSON.stringify({ skill }),
  })
}
