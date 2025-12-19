import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types'
import { apiFetch } from './client'

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
  return apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function logout(): Promise<void> {
  const token = getToken()
  if (!token) return

  try {
    await apiFetch<void>('/auth/logout', {
      method: 'POST',
      requiresAuth: true,
    })
  } finally {
    removeToken()
  }
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>('/api/profile', {
    requiresAuth: true,
  })
}
