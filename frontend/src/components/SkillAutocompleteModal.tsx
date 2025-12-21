import { useState, useEffect, useRef, useCallback } from 'react'
import { X, Search, Plus, Loader2 } from 'lucide-react'
import { getPopularSkills, addCustomSkill } from '../api/skills'

interface SkillAutocompleteModalProps {
  isOpen: boolean
  onClose: () => void
  onAddSkill: (skill: string) => void
  existingSkills: string[]
}

// Minimal fallback list in case API fails or no data
const FALLBACK_SKILLS = [
  'JavaScript', 'TypeScript', 'Python', 'React', 'Node.js', 'Java', 'SQL',
  'AWS', 'Docker', 'Git', 'HTML', 'CSS', 'PostgreSQL', 'MongoDB', 'Redis'
].sort()

export function SkillAutocompleteModal({
  isOpen,
  onClose,
  onAddSkill,
  existingSkills
}: SkillAutocompleteModalProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredSkills, setFilteredSkills] = useState<string[]>([])
  const [allSkills, setAllSkills] = useState<string[]>(FALLBACK_SKILLS)
  const [loadingSkills, setLoadingSkills] = useState(false)
  const [searchingSkills, setSearchingSkills] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load popular skills from API when modal opens
  useEffect(() => {
    if (isOpen && allSkills === FALLBACK_SKILLS) {
      loadPopularSkills()
    }
  }, [isOpen])

  async function loadPopularSkills() {
    setLoadingSkills(true)
    try {
      const response = await getPopularSkills(200)
      if (response.skills.length > 0) {
        setAllSkills(response.skills.sort())
      }
    } catch (error) {
      console.error('Failed to load popular skills, using fallback list:', error)
      // Keep fallback list
    } finally {
      setLoadingSkills(false)
    }
  }

  // Debounced API search for skills not in initial list
  const searchSkillsFromAPI = useCallback(async (term: string) => {
    if (term.length < 2) return

    setSearchingSkills(true)
    try {
      const response = await getPopularSkills(50, term)
      if (response.skills.length > 0) {
        // Merge with existing skills, avoiding duplicates
        setAllSkills(prev => {
          const combined = [...prev]
          for (const skill of response.skills) {
            if (!combined.some(s => s.toLowerCase() === skill.toLowerCase())) {
              combined.push(skill)
            }
          }
          return combined.sort()
        })
      }
    } catch (error) {
      console.error('Failed to search skills:', error)
    } finally {
      setSearchingSkills(false)
    }
  }, [])

  // Filter skills based on search term and exclude existing skills
  useEffect(() => {
    if (searchTerm.trim()) {
      const lowerSearch = searchTerm.toLowerCase()
      const filtered = allSkills.filter(
        skill =>
          skill.toLowerCase().includes(lowerSearch) &&
          !existingSkills.some(existing => existing.toLowerCase() === skill.toLowerCase())
      )
      setFilteredSkills(filtered)
      setHighlightedIndex(0)
    } else {
      setFilteredSkills([])
    }
  }, [searchTerm, existingSkills, allSkills])

  // Debounced API search - only triggered by searchTerm changes
  useEffect(() => {
    if (!searchTerm.trim() || searchTerm.trim().length < 2) {
      return
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = setTimeout(() => {
      searchSkillsFromAPI(searchTerm.trim())
    }, 300)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchTerm, searchSkillsFromAPI])

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Scroll highlighted item into view
  useEffect(() => {
    if (listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [highlightedIndex])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIndex(prev =>
        prev < filteredSkills.length - 1 ? prev + 1 : prev
      )
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIndex(prev => prev > 0 ? prev - 1 : prev)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (filteredSkills.length > 0 && highlightedIndex >= 0) {
        handleSelectSkill(filteredSkills[highlightedIndex])
      } else if (searchTerm.trim()) {
        handleAddCustomSkill()
      }
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  const handleSelectSkill = (skill: string) => {
    onAddSkill(skill)
    setSearchTerm('')
    setFilteredSkills([])
    inputRef.current?.focus()
  }

  const handleAddCustomSkill = async () => {
    const trimmed = searchTerm.trim()
    if (trimmed && !existingSkills.some(s => s.toLowerCase() === trimmed.toLowerCase())) {
      // Save custom skill to database so it appears for other users
      try {
        const result = await addCustomSkill(trimmed)
        console.log('Custom skill saved:', result)

        // Add to local skills list immediately so it appears for this user
        if (!allSkills.includes(trimmed)) {
          setAllSkills(prev => [...prev, trimmed].sort())
        }
      } catch (error) {
        console.error('Failed to save custom skill to database:', error)
        // Continue anyway - user can still add to their profile
      }

      onAddSkill(trimmed)
      setSearchTerm('')
      setFilteredSkills([])
      inputRef.current?.focus()
    }
  }

  if (!isOpen) return null

  const showCustomOption = searchTerm.trim() &&
    !filteredSkills.some(s => s.toLowerCase() === searchTerm.toLowerCase())

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Add Skill</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-4">
          <div className="relative">
            {loadingSkills || searchingSkills ? (
              <Loader2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 animate-spin" />
            ) : (
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            )}
            <input
              ref={inputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={loadingSkills ? "Loading skills..." : "Search or type a skill..."}
              disabled={loadingSkills}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:bg-gray-50 disabled:cursor-wait"
            />
          </div>

          {/* Dropdown Results */}
          {(filteredSkills.length > 0 || showCustomOption) && (
            <div
              ref={listRef}
              className="mt-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg"
            >
              {filteredSkills.map((skill, index) => (
                <button
                  key={skill}
                  onClick={() => handleSelectSkill(skill)}
                  className={`w-full text-left px-4 py-2 hover:bg-indigo-50 transition-colors ${
                    index === highlightedIndex ? 'bg-indigo-50' : ''
                  }`}
                >
                  <span className="text-gray-900">{skill}</span>
                </button>
              ))}

              {/* Custom skill option */}
              {showCustomOption && (
                <button
                  onClick={handleAddCustomSkill}
                  className="w-full text-left px-4 py-2 hover:bg-green-50 transition-colors border-t border-gray-200 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4 text-green-600" />
                  <span className="text-gray-900">
                    Add custom skill: <span className="font-semibold text-green-600">"{searchTerm}"</span>
                  </span>
                </button>
              )}
            </div>
          )}

          {/* Empty state */}
          {searchTerm.trim() && filteredSkills.length === 0 && !showCustomOption && (
            <div className="mt-2 text-center text-gray-500 text-sm py-4">
              No matching skills found
            </div>
          )}

          {/* Helper text */}
          <p className="mt-3 text-xs text-gray-500">
            {loadingSkills
              ? 'Loading popular skills from job market...'
              : `Search from ${allSkills.length} popular skills from real job postings, or add your own custom skill.`
            }
          </p>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
