import type { User, ProfileUpdate, CVUploadResponse, ParsedCV } from '../types'
import { apiFetch } from './client'

export async function getProfile(): Promise<User> {
  return apiFetch<User>('/api/profile', { requiresAuth: true })
}

export async function updateProfile(data: ProfileUpdate): Promise<User> {
  return apiFetch<User>('/api/profile', {
    method: 'PUT',
    requiresAuth: true,
    body: JSON.stringify(data),
  })
}

export async function uploadCV(file: File): Promise<CVUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return apiFetch<CVUploadResponse>('/api/profile/cv', {
    method: 'POST',
    requiresAuth: true,
    body: formData,
  })
}

export async function getParsedCV(): Promise<ParsedCV> {
  return apiFetch<ParsedCV>('/api/profile/cv/parsed', { requiresAuth: true })
}

export async function updateParsedCV(data: Partial<ParsedCV>): Promise<ParsedCV> {
  return apiFetch<ParsedCV>('/api/profile/cv/parsed', {
    method: 'PUT',
    requiresAuth: true,
    body: JSON.stringify(data),
  })
}
