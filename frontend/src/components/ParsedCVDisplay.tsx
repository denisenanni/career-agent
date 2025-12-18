import { useEffect, useState } from 'react'
import { User, Briefcase, GraduationCap, Mail, Phone, FileText, Edit2, Save, X } from 'lucide-react'
import { getParsedCV, updateParsedCV } from '../api/profile'
import { useAuth } from '../contexts/AuthContext'
import { SkillAutocompleteModal } from './SkillAutocompleteModal'
import type { ParsedCV } from '../types'

export function ParsedCVDisplay() {
  const { refreshUser } = useAuth()
  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null)
  const [editedCV, setEditedCV] = useState<ParsedCV | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSkillModal, setShowSkillModal] = useState(false)

  useEffect(() => {
    loadParsedCV()
  }, [])

  async function loadParsedCV() {
    try {
      const data = await getParsedCV()
      setParsedCV(data)
      setEditedCV(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load parsed CV')
    } finally {
      setLoading(false)
    }
  }

  function handleEdit() {
    setIsEditing(true)
    setEditedCV(parsedCV)
  }

  function handleCancel() {
    setIsEditing(false)
    setEditedCV(parsedCV)
  }

  async function handleSave() {
    if (!editedCV) return

    setSaving(true)
    try {
      const updated = await updateParsedCV(editedCV)
      setParsedCV(updated)
      setEditedCV(updated)
      setIsEditing(false)
      // Refresh user profile to sync skills/experience_years
      await refreshUser()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update CV')
    } finally {
      setSaving(false)
    }
  }

  function updateField<K extends keyof ParsedCV>(field: K, value: ParsedCV[K]) {
    if (!editedCV) return
    setEditedCV({ ...editedCV, [field]: value })
  }

  function addSkill(skill: string) {
    if (!editedCV) return
    if (skill && skill.trim()) {
      updateField('skills', [...editedCV.skills, skill.trim()])
    }
  }

  function removeSkill(index: number) {
    if (!editedCV) return
    const skills = editedCV.skills.filter((_, i) => i !== index)
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

  if (error || !parsedCV) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p>{error || 'No CV data available'}</p>
          <p className="text-sm mt-1">Upload a CV to see parsed information</p>
        </div>
      </div>
    )
  }

  const displayCV = isEditing ? editedCV : parsedCV

  if (!displayCV) return null

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Parsed CV Data</h2>
        <div className="flex gap-2">
          {!isEditing ? (
            <button
              onClick={handleEdit}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              <Edit2 className="w-4 h-4" />
              Edit
            </button>
          ) : (
            <>
              <button
                onClick={handleCancel}
                disabled={saving}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Contact Info */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-5 h-5 text-gray-400" />
          {isEditing ? (
            <input
              type="text"
              value={displayCV.name}
              onChange={(e) => updateField('name', e.target.value)}
              className="font-semibold text-gray-900 border-b border-gray-300 focus:border-indigo-500 outline-none"
            />
          ) : (
            <h3 className="font-semibold text-gray-900">{displayCV.name}</h3>
          )}
        </div>
        <div className="ml-7 space-y-1 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4" />
            {isEditing ? (
              <input
                type="email"
                value={displayCV.email || ''}
                onChange={(e) => updateField('email', e.target.value)}
                placeholder="email@example.com"
                className="border-b border-gray-300 focus:border-indigo-500 outline-none"
              />
            ) : displayCV.email ? (
              <span>{displayCV.email}</span>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            {isEditing ? (
              <input
                type="tel"
                value={displayCV.phone || ''}
                onChange={(e) => updateField('phone', e.target.value)}
                placeholder="+1 (555) 123-4567"
                className="border-b border-gray-300 focus:border-indigo-500 outline-none"
              />
            ) : displayCV.phone ? (
              <span>{displayCV.phone}</span>
            ) : null}
          </div>
        </div>
      </div>

      {/* Summary */}
      {(displayCV.summary || isEditing) && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
          {isEditing ? (
            <textarea
              value={displayCV.summary || ''}
              onChange={(e) => updateField('summary', e.target.value)}
              placeholder="Professional summary..."
              rows={3}
              className="w-full text-sm text-gray-600 border border-gray-300 rounded p-2 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          ) : (
            <p className="text-sm text-gray-600">{displayCV.summary}</p>
          )}
        </div>
      )}

      {/* Skills */}
      {(displayCV.skills.length > 0 || isEditing) && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Skills</h3>
            {isEditing && (
              <button
                onClick={() => setShowSkillModal(true)}
                className="text-xs text-indigo-600 hover:text-indigo-700"
              >
                + Add Skill
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {displayCV.skills.map((skill, index) => (
              <span
                key={index}
                className={`px-3 py-1 text-sm rounded-full ${
                  isEditing
                    ? 'bg-indigo-100 text-indigo-700 flex items-center gap-1'
                    : 'bg-indigo-50 text-indigo-700'
                }`}
              >
                {skill}
                {isEditing && (
                  <button
                    onClick={() => removeSkill(index)}
                    className="text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Experience */}
      {displayCV.experience.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Briefcase className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Experience</h3>
            {isEditing ? (
              <input
                type="number"
                value={displayCV.years_of_experience || 0}
                onChange={(e) => updateField('years_of_experience', parseInt(e.target.value) || 0)}
                min="0"
                max="70"
                className="w-16 px-2 py-1 text-sm border border-gray-300 rounded focus:border-indigo-500 outline-none"
              />
            ) : (
              <span className="text-gray-600">({displayCV.years_of_experience} years)</span>
            )}
            {isEditing && <span className="text-sm text-gray-500">years</span>}
          </div>
          <div className="space-y-4 ml-7">
            {displayCV.experience.map((exp, index) => (
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
      {displayCV.education.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <GraduationCap className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Education</h3>
          </div>
          <div className="space-y-3 ml-7">
            {displayCV.education.map((edu, index) => (
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

      {isEditing && error && (
        <div className="text-sm text-red-600 mt-4">
          {error}
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
        existingSkills={editedCV?.skills || []}
      />
    </div>
  )
}
