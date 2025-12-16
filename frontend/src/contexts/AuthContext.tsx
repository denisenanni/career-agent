import { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react'
import type { User, LoginRequest, RegisterRequest } from '../types'
import * as authApi from '../api/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Load user on mount
  useEffect(() => {
    loadUser()
  }, [])

  async function loadUser() {
    try {
      const token = authApi.getToken()
      if (token) {
        const currentUser = await authApi.getCurrentUser()
        setUser(currentUser)
      }
    } catch (error) {
      console.error('Failed to load user:', error)
      authApi.removeToken()
    } finally {
      setLoading(false)
    }
  }

  const login = useCallback(async (data: LoginRequest) => {
    const response = await authApi.login(data)
    authApi.setToken(response.access_token)
    const currentUser = await authApi.getCurrentUser()
    setUser(currentUser)
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    const response = await authApi.register(data)
    authApi.setToken(response.access_token)
    const currentUser = await authApi.getCurrentUser()
    setUser(currentUser)
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }, [])

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
