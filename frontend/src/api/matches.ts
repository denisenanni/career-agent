import type {
  MatchesResponse,
  MatchFilters,
  RefreshMatchesResponse,
  CoverLetterResponse,
  CVHighlightsResponse,
  RegenerateResponse
} from '../types'
import { apiFetch, buildQueryString } from './client'

export async function fetchMatches(filters: MatchFilters = {}): Promise<MatchesResponse> {
  const queryString = buildQueryString(filters)
  return apiFetch<MatchesResponse>(`/api/matches${queryString}`, { requiresAuth: true })
}

export async function refreshMatches(): Promise<RefreshMatchesResponse> {
  return apiFetch<RefreshMatchesResponse>('/api/matches/refresh', {
    method: 'POST',
    requiresAuth: true,
  })
}

export async function updateMatchStatus(matchId: number, status: string): Promise<void> {
  return apiFetch<void>(`/api/matches/${matchId}/status`, {
    method: 'PUT',
    requiresAuth: true,
    body: JSON.stringify({ status }),
  })
}

export async function generateCoverLetter(matchId: number): Promise<CoverLetterResponse> {
  return apiFetch<CoverLetterResponse>(`/api/matches/${matchId}/generate-cover-letter`, {
    method: 'POST',
    requiresAuth: true,
  })
}

export async function generateCVHighlights(matchId: number): Promise<CVHighlightsResponse> {
  return apiFetch<CVHighlightsResponse>(`/api/matches/${matchId}/generate-highlights`, {
    method: 'POST',
    requiresAuth: true,
  })
}

export async function regenerateContent(matchId: number): Promise<RegenerateResponse> {
  return apiFetch<RegenerateResponse>(`/api/matches/${matchId}/regenerate`, {
    method: 'POST',
    requiresAuth: true,
  })
}
