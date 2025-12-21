// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { JobsPage } from '../JobsPage'

// Mock the API
const mockFetchJobs = vi.fn()
const mockRefreshJobs = vi.fn()

vi.mock('../../api/jobs', () => ({
  fetchJobs: (...args: unknown[]) => mockFetchJobs(...args),
  refreshJobs: () => mockRefreshJobs(),
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
    vi.clearAllMocks()
    mockFetchJobs.mockResolvedValue({ jobs: [], total: 0, limit: 50, offset: 0 })
    mockRefreshJobs.mockResolvedValue({ jobs_created: 10, jobs_updated: 5 })
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

  describe('Search', () => {
    it('renders search input', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      expect(screen.getByPlaceholderText(/search jobs/i)).toBeInTheDocument()
    })

    it('updates search value on input', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText(/search jobs/i)

      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'python developer' } })
      })

      expect(searchInput).toHaveValue('python developer')
    })

    it('submits search on form submit', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText(/search jobs/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'react' } })
        fireEvent.click(searchButton)
      })

      await waitFor(() => {
        expect(mockFetchJobs).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'react' })
        )
      })
    })

    it('shows Clear button when search has value', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText(/search jobs/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'java' } })
        fireEvent.click(searchButton)
      })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
      })
    })

    it('clears search when Clear button is clicked', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText(/search jobs/i) as HTMLInputElement
      const searchButton = screen.getByRole('button', { name: /search/i })

      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'node' } })
        fireEvent.click(searchButton)
      })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
      })

      const clearButton = screen.getByRole('button', { name: /clear/i })

      await act(async () => {
        fireEvent.click(clearButton)
      })

      expect(searchInput.value).toBe('')
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no jobs', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchJobs.mockResolvedValue({ jobs: [], total: 0, limit: 50, offset: 0 })

      render(<JobsPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/no jobs available/i)).toBeInTheDocument()
      })
    })

    it('shows no jobs message after search with no results', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchJobs.mockResolvedValue({ jobs: [], total: 0, limit: 50, offset: 0 })

      render(<JobsPage />, { wrapper: createWrapper() })

      const searchInput = screen.getByPlaceholderText(/search jobs/i)
      const searchButton = screen.getByRole('button', { name: /search/i })

      await act(async () => {
        fireEvent.change(searchInput, { target: { value: 'nonexistent' } })
        fireEvent.click(searchButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/no jobs match your search/i)).toBeInTheDocument()
      })
    })
  })

  describe('Jobs Display', () => {
    it('displays jobs when available', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchJobs.mockResolvedValue({
        jobs: [
          {
            id: 1,
            title: 'Senior Python Developer',
            company: 'Tech Corp',
            location: 'Remote',
            url: 'https://example.com/job/1',
            description: 'We are looking for a Python developer.',
            skills: ['Python', 'Django'],
            scraped_at: '2024-01-01T10:00:00Z',
          },
        ],
        total: 1,
        limit: 50,
        offset: 0,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('1 remote jobs available')).toBeInTheDocument()
      })
    })

    it('shows correct plural for multiple jobs', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'user@example.com', is_admin: false, skills: [], preferences: {} },
        loading: false,
      })
      mockFetchJobs.mockResolvedValue({
        jobs: [
          { id: 1, title: 'Job 1', company: 'Co 1', location: 'Remote', url: '#', description: 'Desc 1', skills: [], scraped_at: '2024-01-01' },
          { id: 2, title: 'Job 2', company: 'Co 2', location: 'Remote', url: '#', description: 'Desc 2', skills: [], scraped_at: '2024-01-01' },
        ],
        total: 25,
        limit: 50,
        offset: 0,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('25 remote jobs available')).toBeInTheDocument()
      })
    })
  })

  describe('Refresh Mutation', () => {
    it('triggers refresh mutation when admin clicks refresh', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'admin@example.com', is_admin: true, skills: [], preferences: {} },
        loading: false,
      })

      render(<JobsPage />, { wrapper: createWrapper() })

      const refreshButton = screen.getByRole('button', { name: /refresh jobs/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      await waitFor(() => {
        expect(mockRefreshJobs).toHaveBeenCalled()
      })
    })

    it('disables button while mutation is pending', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'admin@example.com', is_admin: true, skills: [], preferences: {} },
        loading: false,
      })
      mockRefreshJobs.mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<JobsPage />, { wrapper: createWrapper() })

      const refreshButton = screen.getByRole('button', { name: /refresh jobs/i })

      await act(async () => {
        fireEvent.click(refreshButton)
      })

      // Button should be disabled while mutation is pending
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /refreshing/i })
        expect(button).toBeDisabled()
      })
    })
  })
})
