const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  const response = await fetch(`${API_URL}/api/skills/popular?limit=${limit}`)

  if (!response.ok) {
    throw new Error('Failed to fetch popular skills')
  }

  return response.json()
}

export async function addCustomSkill(skill: string): Promise<AddCustomSkillResponse> {
  const response = await fetch(`${API_URL}/api/skills/custom`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ skill }),
  })

  if (!response.ok) {
    throw new Error('Failed to add custom skill')
  }

  return response.json()
}
