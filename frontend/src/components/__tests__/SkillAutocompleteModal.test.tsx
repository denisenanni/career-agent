// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { SkillAutocompleteModal } from '../SkillAutocompleteModal'

// Mock the API
const mockGetPopularSkills = vi.fn()
const mockAddCustomSkill = vi.fn()

vi.mock('../../api/skills', () => ({
  getPopularSkills: (...args: unknown[]) => mockGetPopularSkills(...args),
  addCustomSkill: (...args: unknown[]) => mockAddCustomSkill(...args),
}))

describe('SkillAutocompleteModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onAddSkill: vi.fn(),
    existingSkills: [] as string[],
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetPopularSkills.mockResolvedValue({ skills: ['Python', 'JavaScript', 'React', 'TypeScript'] })
    mockAddCustomSkill.mockResolvedValue({ skill: 'CustomSkill', usage_count: 1 })
  })

  describe('Rendering', () => {
    it('renders nothing when closed', () => {
      render(<SkillAutocompleteModal {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('Add Skill')).not.toBeInTheDocument()
    })

    it('renders modal when open', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      expect(screen.getByText('Add Skill')).toBeInTheDocument()

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search or type/i)).toBeInTheDocument()
      })
    })

    it('loads popular skills on open', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledWith(200)
      })
    })
  })

  describe('Filtering', () => {
    it('filters skills as user types', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      // Wait for skills to load
      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'Py' } })
      })

      // Should show Python in results
      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument()
      })
    })

    it('excludes existing skills from results', async () => {
      render(
        <SkillAutocompleteModal
          {...defaultProps}
          existingSkills={['Python']}
        />
      )

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'Py' } })
      })

      // Wait a bit for filtering
      await new Promise(r => setTimeout(r, 50))

      // Python should NOT be in results since it's in existingSkills
      // But "Add custom skill" might show - check there's no Python button
      const buttons = screen.queryAllByRole('button')
      const pythonButton = buttons.find(b => b.textContent === 'Python')
      expect(pythonButton).toBeUndefined()
    })
  })

  describe('API Search', () => {
    it('calls API for search when typing', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      // Wait for initial load
      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledTimes(1)
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      // Type to trigger search
      await act(async () => {
        fireEvent.change(input, { target: { value: 'test' } })
      })

      // Wait for debounced search (300ms + buffer)
      await act(async () => {
        await new Promise(r => setTimeout(r, 400))
      })

      // Should have made search call
      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledWith(50, 'test')
      })
    })

    it('does not trigger API search for short terms', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledTimes(1)
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      // Type single character
      await act(async () => {
        fireEvent.change(input, { target: { value: 'a' } })
      })

      // Wait past debounce time
      await act(async () => {
        await new Promise(r => setTimeout(r, 400))
      })

      // Should NOT have made additional search (term too short)
      expect(mockGetPopularSkills).toHaveBeenCalledTimes(1)
    })
  })

  describe('No Infinite Loop', () => {
    it('does not create infinite loop when API returns new skills', async () => {
      let callCount = 0
      mockGetPopularSkills.mockImplementation(async (limit, search) => {
        callCount++
        if (callCount > 5) {
          throw new Error('Too many calls - possible infinite loop!')
        }
        if (search) {
          return { skills: ['NewSkill1', 'NewSkill2'] }
        }
        return { skills: ['Python', 'JavaScript'] }
      })

      render(<SkillAutocompleteModal {...defaultProps} />)

      // Wait for initial load
      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledTimes(1)
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      // Type to trigger search
      await act(async () => {
        fireEvent.change(input, { target: { value: 'test' } })
      })

      // Wait for debounced search
      await act(async () => {
        await new Promise(r => setTimeout(r, 400))
      })

      // Wait for search to complete
      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalledTimes(2)
      })

      // Wait more to check for additional unwanted calls
      await act(async () => {
        await new Promise(r => setTimeout(r, 500))
      })

      // Should still only be 2 calls, not infinite
      expect(callCount).toBeLessThanOrEqual(2)
    })
  })

  describe('Selecting Skills', () => {
    it('calls onAddSkill when selecting a skill', async () => {
      const onAddSkill = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onAddSkill={onAddSkill} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'Py' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument()
      })

      await act(async () => {
        fireEvent.click(screen.getByText('Python'))
      })

      expect(onAddSkill).toHaveBeenCalledWith('Python')
    })

    it('clears search after selecting a skill', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i) as HTMLInputElement

      await act(async () => {
        fireEvent.change(input, { target: { value: 'Py' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument()
      })

      await act(async () => {
        fireEvent.click(screen.getByText('Python'))
      })

      expect(input.value).toBe('')
    })
  })

  describe('Custom Skills', () => {
    it('shows option to add custom skill when no match', async () => {
      render(<SkillAutocompleteModal {...defaultProps} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'MyCustomSkill' } })
      })

      await waitFor(() => {
        expect(screen.getByText(/add custom skill/i)).toBeInTheDocument()
      })
    })

    it('saves custom skill to API when added', async () => {
      const onAddSkill = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onAddSkill={onAddSkill} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'MyCustomSkill' } })
      })

      const addButton = await screen.findByText(/add custom skill/i)

      await act(async () => {
        fireEvent.click(addButton)
      })

      await waitFor(() => {
        expect(mockAddCustomSkill).toHaveBeenCalledWith('MyCustomSkill')
        expect(onAddSkill).toHaveBeenCalledWith('MyCustomSkill')
      })
    })
  })

  describe('Keyboard Navigation', () => {
    it('closes modal on Escape', async () => {
      const onClose = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onClose={onClose} />)

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.keyDown(input, { key: 'Escape' })
      })

      expect(onClose).toHaveBeenCalled()
    })

    it('selects skill on Enter', async () => {
      const onAddSkill = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onAddSkill={onAddSkill} />)

      await waitFor(() => {
        expect(mockGetPopularSkills).toHaveBeenCalled()
      })

      const input = await screen.findByPlaceholderText(/search or type/i)

      await act(async () => {
        fireEvent.change(input, { target: { value: 'Py' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Python')).toBeInTheDocument()
      })

      await act(async () => {
        fireEvent.keyDown(input, { key: 'Enter' })
      })

      expect(onAddSkill).toHaveBeenCalledWith('Python')
    })
  })

  describe('Modal Behavior', () => {
    it('closes when clicking backdrop', async () => {
      const onClose = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onClose={onClose} />)

      // Click the backdrop (the outer div with fixed class)
      const backdrop = document.querySelector('.fixed.inset-0')
      if (backdrop) {
        await act(async () => {
          fireEvent.click(backdrop)
        })
        expect(onClose).toHaveBeenCalled()
      }
    })

    it('does not close when clicking modal content', async () => {
      const onClose = vi.fn()
      render(<SkillAutocompleteModal {...defaultProps} onClose={onClose} />)

      // Click the modal title (inside the modal)
      await act(async () => {
        fireEvent.click(screen.getByText('Add Skill'))
      })

      expect(onClose).not.toHaveBeenCalled()
    })
  })
})
