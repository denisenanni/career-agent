import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, X, Search, Loader2 } from 'lucide-react'
import { getSkillsFromJobs } from '../api/skills'

interface SkillsFilterProps {
  selected: string[]
  onChange: (skills: string[]) => void
}

export function SkillsFilter({ selected, onChange }: SkillsFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Fetch skills from jobs when dropdown is open
  const { data: skillsData, isLoading } = useQuery({
    queryKey: ['job-skills', search],
    queryFn: () => getSkillsFromJobs(search || undefined),
    enabled: isOpen,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  const toggleSkill = (skill: string) => {
    if (selected.includes(skill)) {
      onChange(selected.filter(s => s !== skill))
    } else {
      onChange([...selected, skill])
    }
  }

  const removeSkill = (skill: string) => {
    onChange(selected.filter(s => s !== skill))
  }

  const clearAll = () => {
    onChange([])
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected skills as tags */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selected.map(skill => (
            <span
              key={skill}
              className="inline-flex items-center gap-1 bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full text-sm"
            >
              {skill}
              <button
                onClick={() => removeSkill(skill)}
                className="hover:text-indigo-600 focus:outline-none"
                aria-label={`Remove ${skill}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          <button
            onClick={clearAll}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Dropdown trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 text-left border border-gray-300 rounded-md hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        <span className={selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}>
          {selected.length === 0
            ? 'Filter by skills...'
            : `${selected.length} skill${selected.length > 1 ? 's' : ''} selected`}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-80 overflow-hidden">
          {/* Search within skills */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              {isLoading ? (
                <Loader2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
              ) : (
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              )}
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search skills..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Skills list */}
          <div className="max-h-56 overflow-y-auto p-2">
            {isLoading ? (
              <div className="text-center py-4 text-gray-500 text-sm">
                Loading skills...
              </div>
            ) : skillsData?.skills && skillsData.skills.length > 0 ? (
              skillsData.skills.map(({ skill, count }) => (
                <label
                  key={skill}
                  className="flex items-center gap-2 py-2 px-2 hover:bg-gray-50 cursor-pointer rounded"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(skill)}
                    onChange={() => toggleSkill(skill)}
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="flex-1 text-gray-900 text-sm">{skill}</span>
                  <span className="text-gray-400 text-xs">{count}</span>
                </label>
              ))
            ) : (
              <div className="text-center py-4 text-gray-500 text-sm">
                {search ? 'No skills match your search' : 'No skills available'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
