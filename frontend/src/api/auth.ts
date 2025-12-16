import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Token management
export function getToken(): string | null {
  return localStorage.getItem('access_token')
}

export function setToken(token: string): void {
  localStorage.setItem('access_token', token)
}

export function removeToken(): void {
  localStorage.removeItem('access_token')
}

// Auth API calls
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Registration failed')
  }

  return response.json()
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Login failed')
  }

  return response.json()
}

export async function logout(): Promise<void> {
  const token = getToken()
  if (!token) return

  await fetch(`${API_URL}/auth/logout`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  removeToken()
}

export async function getCurrentUser(): Promise<User> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  // Use /api/profile instead of /auth/me to get complete user info including CV data
  const response = await fetch(`${API_URL}/api/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      removeToken()
      throw new Error('Session expired')
    }
    throw new Error('Failed to fetch user')
  }

  return response.json()
}
