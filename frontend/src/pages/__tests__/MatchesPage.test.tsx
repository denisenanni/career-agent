// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { MatchesPage } from '../MatchesPage'

// Mock the API
vi.mock('../../api/matches', () => ({
  fetchMatches: vi.fn().mockResolvedValue({ matches: [], total: 0, limit: 50, offset: 0 }),
  refreshMatches: vi.fn(),
}))

vi.mock('../../api/profile', () => ({
  getProfile: vi.fn().mockResolvedValue({
    id: 1,
    email: 'test@example.com',
    cv_uploaded_at: null,
  }),
}))

// Mock the useAuth hook
const mockUseAuth = vi.fn()
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('MatchesPage', () => {
  beforeEach(() => {
    mockUseAuth.mockClear()
  })

  it('shows Refresh Matches button for admin users', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        email: 'admin@example.com',
        is_admin: true,
        skills: [],
        preferences: {},
      },
      loading: false,
    })

    render(<MatchesPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('button', { name: /refresh matches/i })).toBeInTheDocument()
  })

  it('hides Refresh Matches button for non-admin users', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        email: 'user@example.com',
        is_admin: false,
        skills: [],
        preferences: {},
      },
      loading: false,
    })

    render(<MatchesPage />, { wrapper: createWrapper() })

    expect(screen.queryByRole('button', { name: /refresh matches/i })).not.toBeInTheDocument()
  })

  it('hides Refresh Matches button when user is not logged in', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    })

    render(<MatchesPage />, { wrapper: createWrapper() })

    expect(screen.queryByRole('button', { name: /refresh matches/i })).not.toBeInTheDocument()
  })

  it('shows matches page title', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        email: 'user@example.com',
        is_admin: false,
        skills: [],
        preferences: {},
      },
      loading: false,
    })

    render(<MatchesPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('heading', { name: /your job matches/i })).toBeInTheDocument()
  })
})
