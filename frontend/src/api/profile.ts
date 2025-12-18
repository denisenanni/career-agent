import type { User, ProfileUpdate, CVUploadResponse, ParsedCV } from '../types'
import { getToken } from './auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function getProfile(): Promise<User> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch profile')
  }

  return response.json()
}

export async function updateProfile(data: ProfileUpdate): Promise<User> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/profile`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error('Failed to update profile')
  }

  return response.json()
}

export async function uploadCV(file: File): Promise<CVUploadResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/api/profile/cv`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to upload CV')
  }

  return response.json()
}

export async function getParsedCV(): Promise<ParsedCV> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/profile/cv/parsed`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('No CV uploaded yet')
    }
    throw new Error('Failed to fetch parsed CV')
  }

  return response.json()
}

export async function updateParsedCV(data: Partial<ParsedCV>): Promise<ParsedCV> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/api/profile/cv/parsed`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update parsed CV')
  }

  return response.json()
}
