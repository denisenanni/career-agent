// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { PreferencesForm } from '../PreferencesForm'

// Mock the profile API
const mockUpdateProfile = vi.fn()

vi.mock('../../api/profile', () => ({
  updateProfile: (...args: unknown[]) => mockUpdateProfile(...args),
}))

// Mock AuthContext
const mockUser = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  preferences: {
    min_salary: 100000,
    job_types: ['permanent'],
    remote_types: ['full'],
    preferred_countries: ['United States'],
    eligible_regions: ['US'],
    needs_visa_sponsorship: false,
  },
}

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    refreshUser: vi.fn(),
  }),
}))

describe('PreferencesForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUpdateProfile.mockResolvedValue(mockUser)
  })

  describe('No API calls on mount', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should NOT trigger updateProfile when component mounts with user data', async () => {
      render(<PreferencesForm />)

      // Wait for component to initialize
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Wait past the debounce time (1500ms)
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should NOT have called updateProfile on mount
      expect(mockUpdateProfile).not.toHaveBeenCalled()
    })

    it('should NOT trigger updateProfile when user data loads asynchronously', async () => {
      // Simulate the component rendering before user data is available
      const { rerender } = render(<PreferencesForm />)

      // Initial mount with no user data yet
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Rerender after "user data loads" (simulated by component's useEffect)
      rerender(<PreferencesForm />)

      // Wait past debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should NOT have called updateProfile
      expect(mockUpdateProfile).not.toHaveBeenCalled()
    })
  })

  describe('API calls on user interaction', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should trigger updateProfile when user changes min salary', async () => {
      render(<PreferencesForm />)

      // Wait for initialization
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Find and change the salary input
      const salaryInput = screen.getByLabelText(/minimum salary/i)

      await act(async () => {
        fireEvent.change(salaryInput, { target: { value: '150000' } })
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // NOW it should have called updateProfile
      expect(mockUpdateProfile).toHaveBeenCalledTimes(1)
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        preferences: expect.objectContaining({
          min_salary: 150000,
        }),
      })
    })

    it('should trigger updateProfile when user toggles job type', async () => {
      render(<PreferencesForm />)

      // Wait for initialization
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Find and click the contract checkbox
      const contractCheckbox = screen.getByLabelText(/contract/i)

      await act(async () => {
        fireEvent.click(contractCheckbox)
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should have called updateProfile with updated job_types
      expect(mockUpdateProfile).toHaveBeenCalledTimes(1)
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        preferences: expect.objectContaining({
          job_types: expect.arrayContaining(['permanent', 'contract']),
        }),
      })
    })

    it('should trigger updateProfile when user toggles visa sponsorship', async () => {
      render(<PreferencesForm />)

      // Wait for initialization
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      // Find and click the visa sponsorship checkbox
      const visaCheckbox = screen.getByLabelText(/visa sponsorship/i)

      await act(async () => {
        fireEvent.click(visaCheckbox)
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should have called updateProfile
      expect(mockUpdateProfile).toHaveBeenCalledTimes(1)
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        preferences: expect.objectContaining({
          needs_visa_sponsorship: true,
        }),
      })
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
      render(<PreferencesForm />)

      // Wait for initialization
      await act(async () => {
        vi.advanceTimersByTime(100)
      })

      const salaryInput = screen.getByLabelText(/minimum salary/i)

      // Make multiple rapid changes
      await act(async () => {
        fireEvent.change(salaryInput, { target: { value: '110000' } })
      })
      await act(async () => {
        vi.advanceTimersByTime(500)
      })
      await act(async () => {
        fireEvent.change(salaryInput, { target: { value: '120000' } })
      })
      await act(async () => {
        vi.advanceTimersByTime(500)
      })
      await act(async () => {
        fireEvent.change(salaryInput, { target: { value: '130000' } })
      })

      // Wait for debounce
      await act(async () => {
        vi.advanceTimersByTime(2000)
      })

      // Should only have ONE API call with the final value
      expect(mockUpdateProfile).toHaveBeenCalledTimes(1)
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        preferences: expect.objectContaining({
          min_salary: 130000,
        }),
      })
    })
  })
})
