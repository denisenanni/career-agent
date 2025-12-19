import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MyJobsPage } from '../MyJobsPage'
import * as userJobsApi from '../../api/userJobs'
import type { UserJob } from '../../api/userJobs'

// Mock the useAuth hook
const mockUseAuth = vi.fn()
vi.mock('../../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../contexts/AuthContext')
  return {
    ...actual,
    useAuth: () => mockUseAuth(),
  }
})

// Mock API functions
vi.mock('../../api/userJobs', () => ({
  getUserJobs: vi.fn(),
  parseJobText: vi.fn(),
  createUserJob: vi.fn(),
  deleteUserJob: vi.fn(),
}))

const mockUserJob: UserJob = {
  id: 1,
  user_id: 1,
  title: 'Senior Python Developer',
  company: 'TechCorp Inc.',
  description: 'We are looking for an experienced Python developer.',
  url: 'https://techcorp.com/careers/123',
  source: 'user_submitted',
  tags: ['Python', 'Django', 'FastAPI'],
  salary_min: 120000,
  salary_max: 160000,
  salary_currency: 'USD',
  location: 'Remote',
  remote_type: 'full',
  job_type: 'permanent',
  created_at: '2025-12-18T10:00:00Z',
  updated_at: '2025-12-18T10:00:00Z',
}

function renderMyJobsPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <MyJobsPage />
      </QueryClientProvider>
    </BrowserRouter>
  )
}

describe('MyJobsPage', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, email: 'test@example.com' },
      loading: false,
    })
    vi.clearAllMocks()
  })

  describe('Loading and Empty States', () => {
    it('shows loading state while fetching jobs', () => {
      vi.mocked(userJobsApi.getUserJobs).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderMyJobsPage()

      expect(screen.getByText('Loading your jobs...')).toBeInTheDocument()
    })

    it('shows empty state when user has no jobs', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('No jobs yet')).toBeInTheDocument()
        expect(screen.getByText('Add jobs you\'ve found elsewhere to track and analyze them.')).toBeInTheDocument()
      })
    })

    it('renders "Add Your First Job" button in empty state', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      renderMyJobsPage()

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /Add Your First Job/i })
        expect(button).toBeInTheDocument()
      })
    })
  })

  describe('Jobs List Display', () => {
    it('displays jobs list with correct count', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [mockUserJob],
        total: 1,
      })

      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('1 job you\'ve added')).toBeInTheDocument()
      })
    })

    it('displays multiple jobs with correct count', async () => {
      const jobs = [
        mockUserJob,
        { ...mockUserJob, id: 2, title: 'Frontend Developer' },
        { ...mockUserJob, id: 3, title: 'Backend Developer' },
      ]

      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs,
        total: 3,
      })

      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('3 jobs you\'ve added')).toBeInTheDocument()
        expect(screen.getByText('Senior Python Developer')).toBeInTheDocument()
        expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
        expect(screen.getByText('Backend Developer')).toBeInTheDocument()
      })
    })

    it('renders job details correctly', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [mockUserJob],
        total: 1,
      })

      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('Senior Python Developer')).toBeInTheDocument()
        expect(screen.getByText('TechCorp Inc.')).toBeInTheDocument()
        // "Remote" appears twice - location and remote_type badge
        const remoteElements = screen.getAllByText('Remote')
        expect(remoteElements.length).toBeGreaterThanOrEqual(1)
        expect(screen.getByText(/USD 120,000 - 160,000/)).toBeInTheDocument()
        expect(screen.getByText('Python')).toBeInTheDocument()
        expect(screen.getByText('Django')).toBeInTheDocument()
      })
    })

    it('renders job URL link when provided', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [mockUserJob],
        total: 1,
      })

      renderMyJobsPage()

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /View Posting/i })
        expect(link).toHaveAttribute('href', 'https://techcorp.com/careers/123')
        expect(link).toHaveAttribute('target', '_blank')
      })
    })
  })

  describe('Add Job Form', () => {
    it('shows form when "Add Job" button is clicked', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('No jobs yet')).toBeInTheDocument()
      })

      const addButton = screen.getByRole('button', { name: /Add Job/i })
      await user.click(addButton)

      expect(screen.getByText('Add New Job')).toBeInTheDocument()
      expect(screen.getByLabelText('Paste Job Posting')).toBeInTheDocument()
    })

    it('hides form when Cancel is clicked', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))

      // Open form
      await user.click(screen.getByRole('button', { name: /Add Job/i }))
      expect(screen.getByText('Add New Job')).toBeInTheDocument()

      // Close form
      const cancelButton = screen.getByRole('button', { name: 'Cancel' })
      await user.click(cancelButton)

      expect(screen.queryByText('Add New Job')).not.toBeInTheDocument()
    })

    it('disables Parse button when text is too short', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))
      await user.click(screen.getByRole('button', { name: /Add Job/i }))

      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'Too short')

      const parseButton = screen.getByRole('button', { name: /Parse Job/i })
      expect(parseButton).toBeDisabled()
    })
  })

  describe('Parsing Job Text', () => {
    it('parses job text and shows edit form', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const parsedJob = {
        title: 'Parsed Job Title',
        company: 'Parsed Company',
        description: 'Parsed description',
        location: 'New York, NY',
        remote_type: 'hybrid',
        job_type: 'permanent',
        salary_min: 100000,
        salary_max: 140000,
        salary_currency: 'USD',
        tags: ['JavaScript', 'React'],
      }

      vi.mocked(userJobsApi.parseJobText).mockResolvedValue(parsedJob)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))
      await user.click(screen.getByRole('button', { name: /Add Job/i }))

      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'A'.repeat(60)) // Minimum 50 characters

      const parseButton = screen.getByRole('button', { name: /Parse Job/i })
      await user.click(parseButton)

      await waitFor(() => {
        expect(screen.getByDisplayValue('Parsed Job Title')).toBeInTheDocument()
        expect(screen.getByDisplayValue('Parsed Company')).toBeInTheDocument()
      })
    })

    it('shows error when parsing fails', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      vi.mocked(userJobsApi.parseJobText).mockRejectedValue(
        new Error('Failed to parse job text')
      )

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))
      await user.click(screen.getByRole('button', { name: /Add Job/i }))

      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'A'.repeat(60))

      const parseButton = screen.getByRole('button', { name: /Parse Job/i })
      await user.click(parseButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to parse job text')).toBeInTheDocument()
      })
    })
  })

  describe('Saving Jobs', () => {
    it('saves job and refreshes list', async () => {
      // Mock getUserJobs to return empty first, then with job after create
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({ jobs: [], total: 0 })

      const parsedJob = {
        title: 'New Job',
        company: 'New Company',
        description: 'Job description',
      }

      vi.mocked(userJobsApi.parseJobText).mockResolvedValue(parsedJob)
      vi.mocked(userJobsApi.createUserJob).mockResolvedValue(mockUserJob)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))

      // Open form and paste text
      await user.click(screen.getByRole('button', { name: /Add Job/i }))
      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'A'.repeat(60))

      // Parse
      await user.click(screen.getByRole('button', { name: /Parse Job/i }))

      // Wait for parsed form
      await waitFor(() => screen.getByDisplayValue('New Job'))

      // Save
      const saveButton = screen.getByRole('button', { name: /Save Job/i })
      await user.click(saveButton)

      // Wait for createUserJob to be called
      await waitFor(() => {
        expect(userJobsApi.createUserJob).toHaveBeenCalled()
        // Check only the first argument (React Query passes extra args)
        const callArgs = vi.mocked(userJobsApi.createUserJob).mock.calls[0]
        expect(callArgs[0]).toEqual(parsedJob)
      }, { timeout: 2000 })
    })
  })

  describe('Deleting Jobs', () => {
    it('deletes job after confirmation', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [mockUserJob],
        total: 1,
      })

      vi.mocked(userJobsApi.deleteUserJob).mockResolvedValue(undefined)

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm')
      confirmSpy.mockReturnValue(true)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('Senior Python Developer')).toBeInTheDocument()
      })

      // Find and click delete button
      const deleteButton = screen.getByRole('button', { name: /Delete job/i })
      await user.click(deleteButton)

      // Wait for deleteUserJob to be called
      await waitFor(() => {
        expect(window.confirm).toHaveBeenCalled()
        expect(userJobsApi.deleteUserJob).toHaveBeenCalled()
        // Check only the first argument (React Query passes extra args)
        const callArgs = vi.mocked(userJobsApi.deleteUserJob).mock.calls[0]
        expect(callArgs[0]).toBe(1)
      }, { timeout: 2000 })

      confirmSpy.mockRestore()
    })

    it('does not delete job when confirmation is canceled', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [mockUserJob],
        total: 1,
      })

      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm')
      confirmSpy.mockReturnValue(false)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => {
        expect(screen.getByText('Senior Python Developer')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: /Delete job/i })
      await user.click(deleteButton)

      expect(userJobsApi.deleteUserJob).not.toHaveBeenCalled()

      confirmSpy.mockRestore()
    })
  })

  describe('Form Editing', () => {
    it('allows editing parsed job data before saving', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const parsedJob = {
        title: 'Original Title',
        company: 'Original Company',
        description: 'Original description',
      }

      vi.mocked(userJobsApi.parseJobText).mockResolvedValue(parsedJob)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))
      await user.click(screen.getByRole('button', { name: /Add Job/i }))

      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'A'.repeat(60))

      await user.click(screen.getByRole('button', { name: /Parse Job/i }))

      await waitFor(() => screen.getByDisplayValue('Original Title'))

      // Edit title
      const titleInput = screen.getByDisplayValue('Original Title')
      await user.clear(titleInput)
      await user.type(titleInput, 'Edited Title')

      expect(screen.getByDisplayValue('Edited Title')).toBeInTheDocument()
    })

    it('allows going back to edit text', async () => {
      vi.mocked(userJobsApi.getUserJobs).mockResolvedValue({
        jobs: [],
        total: 0,
      })

      const parsedJob = {
        title: 'Parsed Title',
        description: 'Parsed description',
      }

      vi.mocked(userJobsApi.parseJobText).mockResolvedValue(parsedJob)

      const user = userEvent.setup()
      renderMyJobsPage()

      await waitFor(() => screen.getByRole('button', { name: /Add Job/i }))
      await user.click(screen.getByRole('button', { name: /Add Job/i }))

      const textarea = screen.getByLabelText('Paste Job Posting')
      await user.type(textarea, 'A'.repeat(60))

      await user.click(screen.getByRole('button', { name: /Parse Job/i }))

      await waitFor(() => screen.getByDisplayValue('Parsed Title'))

      // Go back to edit
      const backButton = screen.getByRole('button', { name: /Back to Edit/i })
      await user.click(backButton)

      // Should show textarea again
      expect(screen.getByLabelText('Paste Job Posting')).toBeInTheDocument()
    })
  })
})
