import type {
  MatchesResponse,
  MatchFilters,
  RefreshMatchesResponse,
  CoverLetterResponse,
  CVHighlightsResponse,
  RegenerateResponse
} from '../types'
import { getToken } from './auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function fetchMatches(filters: MatchFilters = {}): Promise<MatchesResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const params = new URLSearchParams()

  if (filters.min_score !== undefined) params.append('min_score', filters.min_score.toString())
  if (filters.status) params.append('status', filters.status)
  if (filters.limit) params.append('limit', filters.limit.toString())
  if (filters.offset) params.append('offset', filters.offset.toString())

  const response = await fetch(`${API_URL}/api/matches?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch matches')
  }

  return response.json()
}

export async function refreshMatches(): Promise<RefreshMatchesResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/matches/refresh`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to refresh matches')
  }

  return response.json()
}

export async function updateMatchStatus(matchId: number, status: string): Promise<void> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/matches/${matchId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ status }),
  })

  if (!response.ok) {
    throw new Error('Failed to update match status')
  }
}

export async function generateCoverLetter(matchId: number): Promise<CoverLetterResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/matches/${matchId}/generate-cover-letter`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to generate cover letter')
  }

  return response.json()
}

export async function generateCVHighlights(matchId: number): Promise<CVHighlightsResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/matches/${matchId}/generate-highlights`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to generate CV highlights')
  }

  return response.json()
}

export async function regenerateContent(matchId: number): Promise<RegenerateResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/matches/${matchId}/regenerate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to regenerate content')
  }

  return response.json()
}
