// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { JobsPage } from '../JobsPage'

// Mock the API
vi.mock('../../api/jobs', () => ({
  fetchJobs: vi.fn().mockResolvedValue({ jobs: [], total: 0, limit: 50, offset: 0 }),
  refreshJobs: vi.fn(),
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

describe('JobsPage', () => {
  beforeEach(() => {
    mockUseAuth.mockClear()
  })

  it('shows Refresh Jobs button for admin users', () => {
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

    render(<JobsPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('button', { name: /refresh jobs/i })).toBeInTheDocument()
  })

  it('hides Refresh Jobs button for non-admin users', () => {
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

    render(<JobsPage />, { wrapper: createWrapper() })

    expect(screen.queryByRole('button', { name: /refresh jobs/i })).not.toBeInTheDocument()
  })

  it('hides Refresh Jobs button when user is not logged in', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    })

    render(<JobsPage />, { wrapper: createWrapper() })

    expect(screen.queryByRole('button', { name: /refresh jobs/i })).not.toBeInTheDocument()
  })

  it('shows jobs page title', () => {
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

    render(<JobsPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('heading', { name: /jobs/i })).toBeInTheDocument()
  })
})
