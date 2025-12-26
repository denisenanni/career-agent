// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import toast from 'react-hot-toast'
import { MatchesPage } from '../MatchesPage'

// Mock the API
const mockFetchMatches = vi.fn()
const mockRefreshMatches = vi.fn()
const mockGetRefreshStatus = vi.fn()
const mockGetProfile = vi.fn()

vi.mock('../../api/matches', () => ({
  fetchMatches: (...args: unknown[]) => mockFetchMatches(...args),
  refreshMatches: () => mockRefreshMatches(),
  getRefreshStatus: () => mockGetRefreshStatus(),
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => {
  const mockToastFn = vi.fn()
  return {
    default: Object.assign(mockToastFn, {
      success: vi.fn(),
      error: vi.fn(),
      loading: vi.fn(),
      dismiss: vi.fn(),
    }),
  }
})

vi.mock('../../api/profile', () => ({
  getProfile: () => mockGetProfile(),
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
    vi.clearAllMocks()
    mockFetchMatches.mockResolvedValue({ matches: [], total: 0, limit: 50, offset: 0 })
    mockGetProfile.mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      cv_uploaded_at: null,
    })
    // New async response format
    mockRefreshMatches.mockResolvedValue({ status: 'processing', message: 'Match refresh started' })
    mockGetRefreshStatus.mockResolvedValue({ status: 'none', message: 'No refresh in progress' })
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

  describe('CV Warning', () => {
    it('shows CV required warning when no CV uploaded', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockGetProfile.mockResolvedValue({ id: 1, email: 'test@example.com', cv_uploaded_at: null })

      render(<MatchesPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/cv required for job matching/i)).toBeInTheDocument()
      })
    })

    it('hides CV warning when CV is uploaded', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockGetProfile.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        cv_uploaded_at: '2024-01-01T12:00:00Z',
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(mockGetProfile).toHaveBeenCalled()
      })

      expect(screen.queryByText(/cv required for job matching/i)).not.toBeInTheDocument()
    })
  })

  describe('Filters', () => {
    it('renders score range filter', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      expect(screen.getByLabelText(/match score range/i)).toBeInTheDocument()
    })

    it('renders status filter', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      expect(screen.getByLabelText(/status/i)).toBeInTheDocument()
    })

    it('changes score range filter and fetches matches', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      const scoreSelect = screen.getByLabelText(/match score range/i)

      await act(async () => {
        fireEvent.change(scoreSelect, { target: { value: '85+' } })
      })

      await waitFor(() => {
        expect(mockFetchMatches).toHaveBeenCalledWith(
          expect.objectContaining({ min_score: 85 })
        )
      })
    })

    it('shows Clear Filters button when filters are modified', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      const statusSelect = screen.getByLabelText(/status/i)

      await act(async () => {
        fireEvent.change(statusSelect, { target: { value: 'applied' } })
      })

      expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no matches', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchMatches.mockResolvedValue({ matches: [], total: 0, limit: 50, offset: 0 })

      render(<MatchesPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/no matches found/i)).toBeInTheDocument()
      })
    })
  })

  describe('Refresh Mutation', () => {
    it('triggers refresh mutation when admin clicks refresh', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'admin@example.com', is_admin: true, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      const refreshButton = screen.getByRole('button', { name: /refresh matches/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      await waitFor(() => {
        expect(mockRefreshMatches).toHaveBeenCalled()
      })
    })

    it('shows loading toast when refresh starts', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'admin@example.com', is_admin: true, skills: [], preferences: {} },
        loading: false,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      const refreshButton = screen.getByRole('button', { name: /refresh matches/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      await waitFor(() => {
        expect(toast.loading).toHaveBeenCalledWith('Refreshing matches...', { id: 'refresh-matches' })
      })
    })
  })

  describe('Matches Display', () => {
    it('displays matches when available', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchMatches.mockResolvedValue({
        matches: [
          {
            id: 1,
            job_id: 101,
            user_id: 1,
            match_score: 85,
            status: 'matched',
            matched_at: '2024-01-01T12:00:00Z',
            reasoning: {
              skill_score: 90,
              location_score: 100,
              salary_score: 80,
              experience_score: 75,
              matching_skills: ['Python', 'React'],
              missing_skills: ['Go'],
              weights: { skills: 0.4, location: 0.2, salary: 0.2, experience: 0.2 },
            },
            job: {
              id: 101,
              title: 'Senior Developer',
              company: 'Tech Corp',
              location: 'Remote',
              description: 'A great job opportunity.',
              url: 'https://example.com/job',
              skills: ['Python', 'React'],
              scraped_at: '2024-01-01T10:00:00Z',
            },
          },
        ],
        total: 1,
        limit: 50,
        offset: 0,
      })

      render(<MatchesPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('1 match found based on your profile')).toBeInTheDocument()
      })
    })
  })
})
