import { apiFetch, buildQueryString } from './client'
import type { SkillsFromJobsResponse } from '../types'

export interface PopularSkillsResponse {
  skills: string[]
  total: number
}

export interface AddCustomSkillResponse {
  skill: string
  created: boolean
  usage_count: number
}

export async function getPopularSkills(limit: number = 200, search?: string): Promise<PopularSkillsResponse> {
  const queryString = buildQueryString({ limit, ...(search && { search }) })
  return apiFetch<PopularSkillsResponse>(`/api/skills/popular${queryString}`)
}

export async function getSkillsFromJobs(search?: string, limit: number = 50): Promise<SkillsFromJobsResponse> {
  const queryString = buildQueryString({ limit, ...(search && { search }) })
  return apiFetch<SkillsFromJobsResponse>(`/api/skills/from-jobs${queryString}`)
}

export async function addCustomSkill(skill: string): Promise<AddCustomSkillResponse> {
  return apiFetch<AddCustomSkillResponse>('/api/skills/custom', {
    method: 'POST',
    body: JSON.stringify({ skill }),
  })
}
