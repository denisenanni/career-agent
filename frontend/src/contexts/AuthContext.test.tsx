// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'

// Mock the auth API
const mockGetToken = vi.fn()
const mockSetToken = vi.fn()
const mockRemoveToken = vi.fn()
const mockLogin = vi.fn()
const mockRegister = vi.fn()
const mockLogout = vi.fn()
const mockGetCurrentUser = vi.fn()

vi.mock('../api/auth', () => ({
  getToken: () => mockGetToken(),
  setToken: (token: string) => mockSetToken(token),
  removeToken: () => mockRemoveToken(),
  login: (data: unknown) => mockLogin(data),
  register: (data: unknown) => mockRegister(data),
  logout: () => mockLogout(),
  getCurrentUser: () => mockGetCurrentUser(),
}))

// Test component to access auth context
function TestComponent({ onAuth }: { onAuth?: (auth: ReturnType<typeof useAuth>) => void }) {
  const auth = useAuth()
  if (onAuth) onAuth(auth)
  return (
    <div>
      <span data-testid="loading">{auth.loading ? 'loading' : 'ready'}</span>
      <span data-testid="user">{auth.user?.email || 'no user'}</span>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetToken.mockReturnValue(null)
    mockGetCurrentUser.mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      skills: [],
      preferences: {},
      is_admin: false,
    })
  })

  describe('AuthProvider', () => {
    it('eventually transitions from loading state', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Should eventually finish loading
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })
    })

    it('loads user when token exists', async () => {
      mockGetToken.mockReturnValue('existing-token')

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      expect(mockGetCurrentUser).toHaveBeenCalled()
    })

    it('sets no user when no token exists', async () => {
      mockGetToken.mockReturnValue(null)

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })

      expect(screen.getByTestId('user')).toHaveTextContent('no user')
      expect(mockGetCurrentUser).not.toHaveBeenCalled()
    })

    it('removes token and sets no user when getCurrentUser fails', async () => {
      mockGetToken.mockReturnValue('invalid-token')
      mockGetCurrentUser.mockRejectedValue(new Error('Unauthorized'))

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })

      expect(mockRemoveToken).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('no user')
    })
  })

  describe('login', () => {
    it('sets token and loads user on successful login', async () => {
      mockLogin.mockResolvedValue({ access_token: 'new-token', token_type: 'bearer' })

      let authContext: ReturnType<typeof useAuth> | undefined

      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth }} />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })

      await act(async () => {
        await authContext!.login({ email: 'user@example.com', password: 'password' })
      })

      expect(mockLogin).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password' })
      expect(mockSetToken).toHaveBeenCalledWith('new-token')
      expect(mockGetCurrentUser).toHaveBeenCalled()
    })
  })

  describe('register', () => {
    it('sets token and loads user on successful registration', async () => {
      mockRegister.mockResolvedValue({ access_token: 'reg-token', token_type: 'bearer' })

      let authContext: ReturnType<typeof useAuth> | undefined

      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth }} />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready')
      })

      await act(async () => {
        await authContext!.register({ email: 'new@example.com', password: 'password' })
      })

      expect(mockRegister).toHaveBeenCalledWith({ email: 'new@example.com', password: 'password' })
      expect(mockSetToken).toHaveBeenCalledWith('reg-token')
      expect(mockGetCurrentUser).toHaveBeenCalled()
    })
  })

  describe('logout', () => {
    it('calls logout API and clears user', async () => {
      mockGetToken.mockReturnValue('existing-token')
      mockLogout.mockResolvedValue(undefined)

      let authContext: ReturnType<typeof useAuth> | undefined

      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth }} />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      await act(async () => {
        await authContext!.logout()
      })

      expect(mockLogout).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('no user')
    })
  })

  describe('refreshUser', () => {
    it('refreshes user data from API', async () => {
      mockGetToken.mockReturnValue('existing-token')

      let authContext: ReturnType<typeof useAuth> | undefined

      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth }} />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      // Change what getCurrentUser returns
      mockGetCurrentUser.mockResolvedValue({
        id: 1,
        email: 'updated@example.com',
        skills: ['Python'],
        preferences: {},
        is_admin: true,
      })

      await act(async () => {
        await authContext!.refreshUser()
      })

      expect(screen.getByTestId('user')).toHaveTextContent('updated@example.com')
    })

    it('handles refresh errors gracefully', async () => {
      mockGetToken.mockReturnValue('existing-token')

      let authContext: ReturnType<typeof useAuth> | undefined

      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth }} />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      // Make refresh fail
      mockGetCurrentUser.mockRejectedValue(new Error('Network error'))

      await act(async () => {
        await authContext!.refreshUser()
      })

      // User should still be the same (not cleared on refresh error)
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })
  })

  describe('useAuth', () => {
    it('throws error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAuth must be used within an AuthProvider')

      consoleSpy.mockRestore()
    })
  })
})
