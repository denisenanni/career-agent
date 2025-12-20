import { useEffect, useState } from 'react'
import { User, Briefcase, GraduationCap, Mail, Phone, FileText } from 'lucide-react'
import { getParsedCV, updateParsedCV } from '../api/profile'
import { useAutoSave } from '../hooks/useAutoSave'
import { SaveStatusIndicator } from './SaveStatusIndicator'
import { SkillAutocompleteModal } from './SkillAutocompleteModal'
import type { ParsedCV } from '../types'

interface ParsedCVDisplayProps {
  refreshTrigger?: number
}

export function ParsedCVDisplay({ refreshTrigger }: ParsedCVDisplayProps = {}) {
  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [showSkillModal, setShowSkillModal] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    loadParsedCV()
  }, [refreshTrigger])

  async function loadParsedCV() {
    setLoading(true)
    setLoadError(null)
    setIsInitialized(false)
    try {
      const data = await getParsedCV()
      setParsedCV(data)
      setIsInitialized(true)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load parsed CV')
    } finally {
      setLoading(false)
    }
  }

  // Auto-save hook
  const { status, error } = useAutoSave({
    data: parsedCV,
    onSave: async (data) => {
      if (!data) return
      const updated = await updateParsedCV(data)
      setParsedCV(updated)
      // Note: refreshUser() removed - updateParsedCV returns updated data
      // and user skills are synced on the backend
    },
    debounceMs: 1500,
    enabled: isInitialized && parsedCV !== null,
  })

  function updateField<K extends keyof ParsedCV>(field: K, value: ParsedCV[K]) {
    if (!parsedCV) return
    setParsedCV({ ...parsedCV, [field]: value })
  }

  function addSkill(skill: string) {
    if (!parsedCV) return
    if (skill && skill.trim()) {
      updateField('skills', [...parsedCV.skills, skill.trim()])
    }
  }

  function removeSkill(index: number) {
    if (!parsedCV) return
    const skills = parsedCV.skills.filter((_, i) => i !== index)
    updateField('skills', skills)
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    )
  }

  if (loadError || !parsedCV) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p>{loadError || 'No CV data available'}</p>
          <p className="text-sm mt-1">Upload a CV to see parsed information</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Parsed CV Data</h2>
        <SaveStatusIndicator status={status} error={error} />
      </div>

      {/* Contact Info */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={parsedCV.name}
            onChange={(e) => updateField('name', e.target.value)}
            className="font-semibold text-gray-900 border-b border-transparent hover:border-gray-300 focus:border-indigo-500 outline-none bg-transparent"
            placeholder="Your name"
          />
        </div>
        <div className="ml-7 space-y-1 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4" />
            <input
              type="email"
              value={parsedCV.email || ''}
              onChange={(e) => updateField('email', e.target.value)}
              placeholder="email@example.com"
              className="border-b border-transparent hover:border-gray-300 focus:border-indigo-500 outline-none bg-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            <input
              type="tel"
              value={parsedCV.phone || ''}
              onChange={(e) => updateField('phone', e.target.value)}
              placeholder="+1 (555) 123-4567"
              className="border-b border-transparent hover:border-gray-300 focus:border-indigo-500 outline-none bg-transparent"
            />
          </div>
        </div>
      </div>

      {/* Summary */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
        <textarea
          value={parsedCV.summary || ''}
          onChange={(e) => updateField('summary', e.target.value)}
          placeholder="Professional summary..."
          rows={3}
          className="w-full text-sm text-gray-600 border border-transparent hover:border-gray-300 focus:border-indigo-500 rounded p-2 focus:ring-1 focus:ring-indigo-500 outline-none bg-transparent resize-none"
        />
      </div>

      {/* Skills */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900">Skills</h3>
          <button
            onClick={() => setShowSkillModal(true)}
            className="text-xs text-indigo-600 hover:text-indigo-700"
          >
            + Add Skill
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {parsedCV.skills.map((skill, index) => (
            <span
              key={index}
              className="px-3 py-1 text-sm rounded-full bg-indigo-100 text-indigo-700 flex items-center gap-1"
            >
              {skill}
              <button
                onClick={() => removeSkill(index)}
                className="text-indigo-600 hover:text-indigo-800 ml-1"
              >
                ×
              </button>
            </span>
          ))}
          {parsedCV.skills.length === 0 && (
            <span className="text-sm text-gray-500">No skills added yet</span>
          )}
        </div>
      </div>

      {/* Experience */}
      {parsedCV.experience.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Briefcase className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Experience</h3>
            <input
              type="number"
              value={parsedCV.years_of_experience || 0}
              onChange={(e) => updateField('years_of_experience', parseInt(e.target.value) || 0)}
              min="0"
              max="70"
              className="w-16 px-2 py-1 text-sm border border-transparent hover:border-gray-300 focus:border-indigo-500 rounded outline-none bg-transparent"
            />
            <span className="text-sm text-gray-500">years</span>
          </div>
          <div className="space-y-4 ml-7">
            {parsedCV.experience.map((exp, index) => (
              <div key={index} className="border-l-2 border-gray-200 pl-4">
                <h4 className="font-medium text-gray-900">{exp.title}</h4>
                <p className="text-sm text-gray-600">{exp.company}</p>
                <p className="text-xs text-gray-500 mb-1">
                  {exp.start_date} - {exp.end_date || 'Present'}
                </p>
                <p className="text-sm text-gray-600 whitespace-pre-line">{exp.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {parsedCV.education.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <GraduationCap className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Education</h3>
          </div>
          <div className="space-y-3 ml-7">
            {parsedCV.education.map((edu, index) => (
              <div key={index}>
                <h4 className="font-medium text-gray-900">{edu.degree}</h4>
                <p className="text-sm text-gray-600">{edu.institution}</p>
                {edu.field && <p className="text-sm text-gray-600">{edu.field}</p>}
                {edu.end_date && <p className="text-xs text-gray-500">{edu.end_date}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Autocomplete Modal */}
      <SkillAutocompleteModal
        isOpen={showSkillModal}
        onClose={() => setShowSkillModal(false)}
        onAddSkill={(skill) => {
          addSkill(skill)
          setShowSkillModal(false)
        }}
        existingSkills={parsedCV.skills}
      />
    </div>
  )
}
