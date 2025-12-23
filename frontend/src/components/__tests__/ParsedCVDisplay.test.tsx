// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { ParsedCVDisplay } from '../ParsedCVDisplay'

// Mock the profile API
const mockGetParsedCV = vi.fn()
const mockUpdateParsedCV = vi.fn()

vi.mock('../../api/profile', () => ({
  getParsedCV: (...args: unknown[]) => mockGetParsedCV(...args),
  updateParsedCV: (...args: unknown[]) => mockUpdateParsedCV(...args),
}))

// Mock the skills API
vi.mock('../../api/skills', () => ({
  getPopularSkills: vi.fn().mockResolvedValue({ skills: ['Python', 'JavaScript'] }),
  addCustomSkill: vi.fn().mockResolvedValue({ skill: 'Custom', usage_count: 1 }),
}))

const mockParsedCV = {
  name: 'John Doe',
  email: 'john@example.com',
  phone: '+1234567890',
  summary: 'Experienced software developer',
  skills: ['Python', 'JavaScript', 'React'],
  experience: [
    {
      title: 'Senior Developer',
      company: 'Tech Corp',
      start_date: '2020-01',
      end_date: null,
      description: 'Building amazing software',
    },
  ],
  education: [
    {
      degree: 'BS Computer Science',
      institution: 'State University',
      field: 'Computer Science',
      end_date: '2019',
    },
  ],
  years_of_experience: 5,
}

describe('ParsedCVDisplay', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Make the mock return immediately
    mockGetParsedCV.mockResolvedValue(mockParsedCV)
    mockUpdateParsedCV.mockResolvedValue(mockParsedCV)
  })

  describe('No API calls on mount', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should NOT trigger updateParsedCV when component mounts and loads data', async () => {
      // Need to flush promises for the API mock to resolve with fake timers
      mockGetParsedCV.mockImplementation(() => Promise.resolve(mockParsedCV))

      await act(async () => {
        render(<ParsedCVDisplay />)
      })

      // Flush pending promises
      await act(async () => {
        await Promise.resolve()
      })

      // Wait for component to finish loading
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Wait past the debounce time (1500ms)
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // getParsedCV should have been called (to load data)
      expect(mockGetParsedCV).toHaveBeenCalledTimes(1)

      // But updateParsedCV should NOT have been called on mount
      expect(mockUpdateParsedCV).not.toHaveBeenCalled()
    })
  })

  describe('API calls on user interaction', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should trigger updateParsedCV when user changes name', async () => {
      mockGetParsedCV.mockImplementation(() => Promise.resolve(mockParsedCV))

      await act(async () => {
        render(<ParsedCVDisplay />)
      })

      // Flush promises for data to load
      await act(async () => {
        await Promise.resolve()
        vi.advanceTimersByTime(100)
      })

      // Find and change the name input
      const nameInput = screen.getByDisplayValue('John Doe')

      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'Jane Doe' } })
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // NOW it should have called updateParsedCV
      expect(mockUpdateParsedCV).toHaveBeenCalledTimes(1)
      expect(mockUpdateParsedCV).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Jane Doe',
        })
      )
    })

    it('should trigger updateParsedCV when user changes email', async () => {
      mockGetParsedCV.mockImplementation(() => Promise.resolve(mockParsedCV))

      await act(async () => {
        render(<ParsedCVDisplay />)
      })

      await act(async () => {
        await Promise.resolve()
        vi.advanceTimersByTime(100)
      })

      const emailInput = screen.getByDisplayValue('john@example.com')

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'jane@example.com' } })
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      expect(mockUpdateParsedCV).toHaveBeenCalledTimes(1)
      expect(mockUpdateParsedCV).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'jane@example.com',
        })
      )
    })

    it('should trigger updateParsedCV when user removes a skill', async () => {
      mockGetParsedCV.mockImplementation(() => Promise.resolve(mockParsedCV))

      await act(async () => {
        render(<ParsedCVDisplay />)
      })

      await act(async () => {
        await Promise.resolve()
        vi.advanceTimersByTime(100)
      })

      // Find the remove button for Python skill
      const pythonSkill = screen.getByText('Python').closest('span')
      const removeButton = pythonSkill?.querySelector('button')

      await act(async () => {
        if (removeButton) {
          fireEvent.click(removeButton)
        }
      })

      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      expect(mockUpdateParsedCV).toHaveBeenCalledTimes(1)
      expect(mockUpdateParsedCV).toHaveBeenCalledWith(
        expect.objectContaining({
          skills: ['JavaScript', 'React'], // Python removed
        })
      )
    })
  })

  describe('Debouncing behavior', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should debounce multiple rapid changes into single API call', async () => {
      mockGetParsedCV.mockImplementation(() => Promise.resolve(mockParsedCV))

      await act(async () => {
        render(<ParsedCVDisplay />)
      })

      await act(async () => {
        await Promise.resolve()
        vi.advanceTimersByTime(100)
      })

      const nameInput = screen.getByDisplayValue('John Doe')

      // Make multiple rapid changes
      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'Jane' } })
      })
      await act(async () => {
        vi.advanceTimersByTime(500)
      })
      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'Jane D' } })
      })
      await act(async () => {
        vi.advanceTimersByTime(500)
      })
      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'Jane Doe' } })
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should only have ONE API call with the final value
      expect(mockUpdateParsedCV).toHaveBeenCalledTimes(1)
      expect(mockUpdateParsedCV).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Jane Doe',
        })
      )
    })
  })

  describe('Loading and error states', () => {
    it('should show error state when API fails', async () => {
      mockGetParsedCV.mockRejectedValue(new Error('Failed to fetch'))

      render(<ParsedCVDisplay />)

      await waitFor(() => {
        expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument()
      })

      // Should NOT have called update
      expect(mockUpdateParsedCV).not.toHaveBeenCalled()
    })

    it('should show empty state when no CV data', async () => {
      mockGetParsedCV.mockResolvedValue(null)

      render(<ParsedCVDisplay />)

      await waitFor(() => {
        expect(screen.getByText(/no cv data available/i)).toBeInTheDocument()
      })

      // Should NOT have called update
      expect(mockUpdateParsedCV).not.toHaveBeenCalled()
    })
  })
})
