import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MatchCard } from './MatchCard'
import type { Match } from '../types'
import * as matchesApi from '../api/matches'

// Mock the matches API
vi.mock('../api/matches', () => ({
  updateMatchStatus: vi.fn(),
}))

const mockMatch: Match = {
  id: 1,
  job_id: 10,
  score: 85,
  status: 'matched',
  reasoning: {
    overall_score: 85,
    skill_score: 90,
    location_score: 75,
    salary_score: 80,
    experience_score: 85,
    matching_skills: ['React', 'TypeScript', 'Node.js'],
    missing_skills: ['Python', 'Go'],
    weights: {
      skills: 0.4,
      location: 0.2,
      salary: 0.2,
      experience: 0.2,
    },
  },
  analysis: 'This is a great match based on your skills and experience.',
  created_at: '2024-01-15T10:00:00Z',
  job_title: 'Senior Frontend Developer',
  job_company: 'Tech Corp',
  job_url: 'https://example.com/job/123',
  job_location: 'San Francisco, CA',
  job_remote_type: 'hybrid',
  job_salary_min: 120000,
  job_salary_max: 180000,
}

function renderMatchCard(match: Match = mockMatch) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MatchCard match={match} />
    </QueryClientProvider>
  )
}

describe('MatchCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render match information correctly', () => {
    renderMatchCard()

    expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument()
    expect(screen.getByText('Tech Corp')).toBeInTheDocument()
    // 85% appears multiple times (main score + experience score)
    expect(screen.getAllByText('85%').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Excellent Match')).toBeInTheDocument()
    expect(screen.getByText('San Francisco, CA')).toBeInTheDocument()
    expect(screen.getByText('$120,000 - $180,000')).toBeInTheDocument()
  })

  it('should show matching skills', () => {
    renderMatchCard()

    expect(screen.getByText('✓ React')).toBeInTheDocument()
    expect(screen.getByText('✓ TypeScript')).toBeInTheDocument()
    expect(screen.getByText('✓ Node.js')).toBeInTheDocument()
  })

  it('should show missing skills', () => {
    renderMatchCard()

    expect(screen.getByText('✗ Python')).toBeInTheDocument()
    expect(screen.getByText('✗ Go')).toBeInTheDocument()
  })

  it('should show breakdown scores', () => {
    renderMatchCard()

    expect(screen.getByText('90%')).toBeInTheDocument() // Skills
    expect(screen.getByText('75%')).toBeInTheDocument() // Location
    expect(screen.getByText('80%')).toBeInTheDocument() // Salary
    // 85% appears multiple times (Experience score + Total score badge)
    expect(screen.getAllByText('85%').length).toBeGreaterThanOrEqual(1)
  })

  it('should update status to interested when clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(matchesApi.updateMatchStatus).mockResolvedValueOnce()

    renderMatchCard()

    const interestedButton = screen.getByRole('button', { name: /mark interested/i })
    await user.click(interestedButton)

    await waitFor(() => {
      expect(matchesApi.updateMatchStatus).toHaveBeenCalledWith(1, 'interested')
    })
  })

  it('should update status to applied when clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(matchesApi.updateMatchStatus).mockResolvedValueOnce()

    renderMatchCard()

    const appliedButton = screen.getByRole('button', { name: /mark applied/i })
    await user.click(appliedButton)

    await waitFor(() => {
      expect(matchesApi.updateMatchStatus).toHaveBeenCalledWith(1, 'applied')
    })
  })

  it('should show interested status when match is interested', () => {
    const interestedMatch = { ...mockMatch, status: 'interested' as const }
    renderMatchCard(interestedMatch)

    expect(screen.getByText('✓ Interested')).toBeInTheDocument()
    const interestedButton = screen.getByRole('button', { name: /✓ interested/i })
    expect(interestedButton).toBeDisabled()
  })

  it('should show both interested and applied when status is applied', () => {
    const appliedMatch = { ...mockMatch, status: 'applied' as const }
    renderMatchCard(appliedMatch)

    expect(screen.getByText('✓ Interested')).toBeInTheDocument()
    expect(screen.getByText('✓ Applied')).toBeInTheDocument()

    const interestedButton = screen.getByRole('button', { name: /✓ interested/i })
    const appliedButton = screen.getByRole('button', { name: /✓ applied/i })

    expect(interestedButton).toBeDisabled()
    expect(appliedButton).toBeDisabled()
  })

  it('should hide match when hide button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(matchesApi.updateMatchStatus).mockResolvedValueOnce()

    renderMatchCard()

    const hideButton = screen.getByRole('button', { name: /hide/i })
    await user.click(hideButton)

    await waitFor(() => {
      expect(matchesApi.updateMatchStatus).toHaveBeenCalledWith(1, 'hidden')
    })
  })

  it('should toggle details when show details button is clicked', async () => {
    const user = userEvent.setup()
    renderMatchCard()

    // Details should be hidden initially
    expect(screen.queryByText(/matching algorithm weights/i)).not.toBeInTheDocument()

    const toggleButton = screen.getByRole('button', { name: /show details/i })
    await user.click(toggleButton)

    // Details should be visible
    await waitFor(() => {
      expect(screen.getByText(/matching algorithm weights/i)).toBeInTheDocument()
    })

    // Click again to hide
    await user.click(screen.getByRole('button', { name: /hide details/i }))

    // Details should be hidden again
    await waitFor(() => {
      expect(screen.queryByText(/matching algorithm weights/i)).not.toBeInTheDocument()
    })
  })

  it('should display score color based on score value', () => {
    const { container: container85 } = renderMatchCard({ ...mockMatch, score: 85 })
    expect(container85.querySelector('.text-green-700')).toBeInTheDocument()

    const { container: container75 } = renderMatchCard({ ...mockMatch, score: 75 })
    expect(container75.querySelector('.text-blue-700')).toBeInTheDocument()

    const { container: container65 } = renderMatchCard({ ...mockMatch, score: 65 })
    expect(container65.querySelector('.text-yellow-700')).toBeInTheDocument()
  })

  it('should format salary correctly for min and max', () => {
    renderMatchCard()
    expect(screen.getByText('$120,000 - $180,000')).toBeInTheDocument()
  })

  it('should format salary correctly for min only', () => {
    const matchMinOnly = { ...mockMatch, job_salary_max: null }
    renderMatchCard(matchMinOnly)
    expect(screen.getByText('$120,000+')).toBeInTheDocument()
  })

  it('should not show salary if both min and max are null', () => {
    const matchNoSalary = { ...mockMatch, job_salary_min: null, job_salary_max: null }
    renderMatchCard(matchNoSalary)
    expect(screen.queryByText(/\$/)).not.toBeInTheDocument()
  })

  it('should show remote type correctly', () => {
    renderMatchCard()
    expect(screen.getByText('hybrid')).toBeInTheDocument()
  })

  it('should show "Remote" for full remote type', () => {
    const remoteMatch = { ...mockMatch, job_remote_type: 'full' }
    renderMatchCard(remoteMatch)
    expect(screen.getByText('Remote')).toBeInTheDocument()
  })

  it('should link to job URL', () => {
    renderMatchCard()
    const link = screen.getByRole('link', { name: /senior frontend developer/i })
    expect(link).toHaveAttribute('href', 'https://example.com/job/123')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('should limit displayed matching skills to 10', () => {
    const manySkillsMatch = {
      ...mockMatch,
      reasoning: {
        ...mockMatch.reasoning,
        matching_skills: Array(15).fill('Skill').map((s, i) => `${s}${i + 1}`),
      },
    }
    renderMatchCard(manySkillsMatch)

    // Should show first 10
    expect(screen.getByText('✓ Skill1')).toBeInTheDocument()
    expect(screen.getByText('✓ Skill10')).toBeInTheDocument()
    // Should not show 11th
    expect(screen.queryByText('✓ Skill11')).not.toBeInTheDocument()
    // Should show "+5 more"
    expect(screen.getByText('+5 more')).toBeInTheDocument()
  })

  it('should limit displayed missing skills to 8', () => {
    const manyMissingSkillsMatch = {
      ...mockMatch,
      reasoning: {
        ...mockMatch.reasoning,
        missing_skills: Array(12).fill('Missing').map((s, i) => `${s}${i + 1}`),
      },
    }
    renderMatchCard(manyMissingSkillsMatch)

    // Should show first 8
    expect(screen.getByText('✗ Missing1')).toBeInTheDocument()
    expect(screen.getByText('✗ Missing8')).toBeInTheDocument()
    // Should not show 9th
    expect(screen.queryByText('✗ Missing9')).not.toBeInTheDocument()
    // Should show "+4 more"
    expect(screen.getByText('+4 more')).toBeInTheDocument()
  })

  it('should show application materials button', () => {
    renderMatchCard()
    expect(screen.getByRole('button', { name: /generate application materials/i })).toBeInTheDocument()
  })
})
