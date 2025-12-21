// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getToken, setToken, removeToken, register, login, logout, getCurrentUser } from './auth'

// Mock apiFetch
const mockApiFetch = vi.fn()
vi.mock('./client', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}))

describe('auth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Token Management', () => {
    it('getToken returns null when no token exists', () => {
      expect(getToken()).toBeNull()
    })

    it('setToken stores token in localStorage', () => {
      setToken('test-token')
      expect(localStorage.getItem('access_token')).toBe('test-token')
    })

    it('getToken returns stored token', () => {
      localStorage.setItem('access_token', 'my-token')
      expect(getToken()).toBe('my-token')
    })

    it('removeToken clears token from localStorage', () => {
      localStorage.setItem('access_token', 'my-token')
      removeToken()
      expect(localStorage.getItem('access_token')).toBeNull()
    })
  })

  describe('register', () => {
    it('calls apiFetch with correct parameters', async () => {
      const mockResponse = { access_token: 'new-token', token_type: 'bearer' }
      mockApiFetch.mockResolvedValue(mockResponse)

      const data = { email: 'test@example.com', password: 'password123' }
      const result = await register(data)

      expect(mockApiFetch).toHaveBeenCalledWith('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      expect(result).toEqual(mockResponse)
    })

    it('propagates errors from apiFetch', async () => {
      mockApiFetch.mockRejectedValue(new Error('Registration failed'))

      await expect(register({ email: 'test@example.com', password: 'pass' }))
        .rejects.toThrow('Registration failed')
    })
  })

  describe('login', () => {
    it('calls apiFetch with correct parameters', async () => {
      const mockResponse = { access_token: 'login-token', token_type: 'bearer' }
      mockApiFetch.mockResolvedValue(mockResponse)

      const data = { email: 'user@example.com', password: 'secret' }
      const result = await login(data)

      expect(mockApiFetch).toHaveBeenCalledWith('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      expect(result).toEqual(mockResponse)
    })

    it('propagates errors from apiFetch', async () => {
      mockApiFetch.mockRejectedValue(new Error('Invalid credentials'))

      await expect(login({ email: 'bad@example.com', password: 'wrong' }))
        .rejects.toThrow('Invalid credentials')
    })
  })

  describe('logout', () => {
    it('calls apiFetch and removes token', async () => {
      mockApiFetch.mockResolvedValue(undefined)
      localStorage.setItem('access_token', 'my-token')

      await logout()

      expect(mockApiFetch).toHaveBeenCalledWith('/auth/logout', {
        method: 'POST',
        requiresAuth: true,
      })
      expect(localStorage.getItem('access_token')).toBeNull()
    })

    it('does nothing if no token exists', async () => {
      await logout()

      expect(mockApiFetch).not.toHaveBeenCalled()
    })

    it('removes token even if API call fails', async () => {
      mockApiFetch.mockRejectedValue(new Error('Server error'))
      localStorage.setItem('access_token', 'my-token')

      // logout throws the error but still removes the token in finally block
      try {
        await logout()
      } catch {
        // Expected to throw
      }

      // Token should still be removed even though API failed
      expect(localStorage.getItem('access_token')).toBeNull()
    })
  })

  describe('getCurrentUser', () => {
    it('calls apiFetch with correct parameters', async () => {
      const mockUser = {
        id: 1,
        email: 'user@example.com',
        skills: ['Python'],
        preferences: {},
        is_admin: false,
      }
      mockApiFetch.mockResolvedValue(mockUser)

      const result = await getCurrentUser()

      expect(mockApiFetch).toHaveBeenCalledWith('/api/profile', {
        requiresAuth: true,
      })
      expect(result).toEqual(mockUser)
    })

    it('propagates errors from apiFetch', async () => {
      mockApiFetch.mockRejectedValue(new Error('Unauthorized'))

      await expect(getCurrentUser()).rejects.toThrow('Unauthorized')
    })
  })
})
