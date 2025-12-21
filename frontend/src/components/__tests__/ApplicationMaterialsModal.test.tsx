// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationMaterialsModal } from '../ApplicationMaterialsModal'

// Mock the API
const mockGenerateCoverLetter = vi.fn()
const mockGenerateCVHighlights = vi.fn()
const mockRegenerateContent = vi.fn()

vi.mock('../../api/matches', () => ({
  generateCoverLetter: (...args: unknown[]) => mockGenerateCoverLetter(...args),
  generateCVHighlights: (...args: unknown[]) => mockGenerateCVHighlights(...args),
  regenerateContent: (...args: unknown[]) => mockRegenerateContent(...args),
}))

// Mock clipboard API
const mockWriteText = vi.fn()
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
})

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('ApplicationMaterialsModal', () => {
  const defaultProps = {
    matchId: 123,
    jobTitle: 'Software Engineer',
    company: 'Tech Corp',
    onClose: vi.fn(),
  }

  const mockCoverLetterData = {
    cover_letter: 'Dear Hiring Manager...',
    cached: false,
    generated_at: '2024-01-01T12:00:00Z',
  }

  const mockHighlightsData = {
    highlights: ['5 years Python experience', 'Led team of 10', 'AWS certified'],
    cached: false,
    generated_at: '2024-01-01T12:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGenerateCoverLetter.mockResolvedValue(mockCoverLetterData)
    mockGenerateCVHighlights.mockResolvedValue(mockHighlightsData)
    mockRegenerateContent.mockResolvedValue({})
  })

  describe('Rendering', () => {
    it('renders modal with correct title', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByText('Application Materials')).toBeInTheDocument()
      expect(screen.getByText('Software Engineer at Tech Corp')).toBeInTheDocument()
    })

    it('shows cover letter tab as active by default', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      const coverLetterTab = screen.getByRole('button', { name: /cover letter/i })
      expect(coverLetterTab).toHaveClass('border-indigo-600')
    })

    it('auto-generates content on mount', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(mockGenerateCoverLetter).toHaveBeenCalledWith(123)
        expect(mockGenerateCVHighlights).toHaveBeenCalledWith(123)
      })
    })
  })

  describe('Cover Letter Tab', () => {
    it('shows loading state while generating', async () => {
      mockGenerateCoverLetter.mockImplementation(() => new Promise(() => {})) // Never resolves
      mockGenerateCVHighlights.mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Generating cover letter...')).toBeInTheDocument()
      })
    })

    it('displays generated cover letter', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })
    })

    it('shows error state on failure', async () => {
      mockGenerateCoverLetter.mockRejectedValue(new Error('API Error'))

      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/failed to generate cover letter/i)).toBeInTheDocument()
      })
    })

    it('shows cached indicator when data is cached', async () => {
      mockGenerateCoverLetter.mockResolvedValue({ ...mockCoverLetterData, cached: true })

      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/cached/i)).toBeInTheDocument()
      })
    })

    it('copies cover letter to clipboard', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })

      const copyButton = screen.getByRole('button', { name: /copy/i })
      await act(async () => {
        fireEvent.click(copyButton)
      })

      expect(mockWriteText).toHaveBeenCalledWith('Dear Hiring Manager...')
    })
  })

  describe('CV Highlights Tab', () => {
    it('switches to highlights tab', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      const highlightsTab = screen.getByRole('button', { name: /cv highlights/i })
      await act(async () => {
        fireEvent.click(highlightsTab)
      })

      expect(highlightsTab).toHaveClass('border-indigo-600')
    })

    it('displays highlights as numbered list', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      // Switch to highlights tab
      const highlightsTab = screen.getByRole('button', { name: /cv highlights/i })
      await act(async () => {
        fireEvent.click(highlightsTab)
      })

      await waitFor(() => {
        expect(screen.getByText('5 years Python experience')).toBeInTheDocument()
        expect(screen.getByText('Led team of 10')).toBeInTheDocument()
        expect(screen.getByText('AWS certified')).toBeInTheDocument()
      })
    })

    it('shows error state on failure', async () => {
      mockGenerateCVHighlights.mockRejectedValue(new Error('API Error'))

      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      // Switch to highlights tab
      const highlightsTab = screen.getByRole('button', { name: /cv highlights/i })
      await act(async () => {
        fireEvent.click(highlightsTab)
      })

      await waitFor(() => {
        expect(screen.getByText(/failed to generate cv highlights/i)).toBeInTheDocument()
      })
    })
  })

  describe('Regenerate', () => {
    it('shows regenerate confirmation when clicked', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })

      const regenerateButton = screen.getByRole('button', { name: /regenerate/i })
      await act(async () => {
        fireEvent.click(regenerateButton)
      })

      expect(screen.getByText('Regenerate all content?')).toBeInTheDocument()
    })

    it('cancels regenerate confirmation', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })

      const regenerateButton = screen.getByRole('button', { name: /regenerate/i })
      await act(async () => {
        fireEvent.click(regenerateButton)
      })

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await act(async () => {
        fireEvent.click(cancelButton)
      })

      expect(screen.queryByText('Regenerate all content?')).not.toBeInTheDocument()
    })

    it('regenerates content when confirmed', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })

      // Click regenerate
      const regenerateButton = screen.getByRole('button', { name: /regenerate/i })
      await act(async () => {
        fireEvent.click(regenerateButton)
      })

      // Confirm
      const yesButton = screen.getByRole('button', { name: /yes/i })
      await act(async () => {
        fireEvent.click(yesButton)
      })

      await waitFor(() => {
        expect(mockRegenerateContent).toHaveBeenCalledWith(123)
      })
    })
  })

  describe('Modal Actions', () => {
    it('closes modal when X button clicked', async () => {
      const onClose = vi.fn()
      render(<ApplicationMaterialsModal {...defaultProps} onClose={onClose} />, {
        wrapper: createWrapper(),
      })

      const closeButton = screen.getByRole('button', { name: '×' })
      await act(async () => {
        fireEvent.click(closeButton)
      })

      expect(onClose).toHaveBeenCalled()
    })

    it('has download button when cover letter is ready', async () => {
      render(<ApplicationMaterialsModal {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByDisplayValue('Dear Hiring Manager...')).toBeInTheDocument()
      })

      const downloadButton = screen.getByRole('button', { name: /download/i })
      expect(downloadButton).toBeInTheDocument()
    })
  })
})
