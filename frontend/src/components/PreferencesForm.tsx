import { useState, useEffect } from 'react'
import { Settings, CheckCircle, AlertCircle } from 'lucide-react'
import { updateProfile } from '../api/profile'
import { useAuth } from '../contexts/AuthContext'

export function PreferencesForm() {
  const { user, refreshUser } = useAuth()
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [minSalary, setMinSalary] = useState<number | ''>('')
  const [jobType, setJobType] = useState<string>('')
  const [remoteType, setRemoteType] = useState<string>('')
  const [location, setLocation] = useState<string>('')

  // Load current preferences
  useEffect(() => {
    if (user?.preferences) {
      setMinSalary(user.preferences.min_salary || '')
      setJobType(user.preferences.job_type || '')
      setRemoteType(user.preferences.remote_type || '')
      setLocation(user.preferences.location || '')
    }
  }, [user])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setSaving(true)

    try {
      // Build preferences object
      const preferences: Record<string, any> = {}

      if (minSalary !== '') preferences.min_salary = Number(minSalary)
      if (jobType) preferences.job_type = jobType
      if (remoteType) preferences.remote_type = remoteType
      if (location) preferences.location = location

      await updateProfile({ preferences })
      await refreshUser()
      setSuccess(true)

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-5 h-5 text-gray-400" />
        <h2 className="text-lg font-semibold text-gray-900">Job Preferences</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="minSalary" className="block text-sm font-medium text-gray-700">
            Minimum Salary (USD/year)
          </label>
          <input
            id="minSalary"
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value ? Number(e.target.value) : '')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
            placeholder="120000"
            min="0"
            step="1000"
          />
        </div>

        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700">
            Preferred Location
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
            placeholder="e.g., San Francisco, Remote"
          />
        </div>

        <div>
          <label htmlFor="jobType" className="block text-sm font-medium text-gray-700">
            Job Type
          </label>
          <select
            id="jobType"
            value={jobType}
            onChange={(e) => setJobType(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
          >
            <option value="">Any</option>
            <option value="permanent">Permanent</option>
            <option value="contract">Contract</option>
            <option value="freelance">Freelance</option>
            <option value="part-time">Part-time</option>
          </select>
        </div>

        <div>
          <label htmlFor="remoteType" className="block text-sm font-medium text-gray-700">
            Remote Type
          </label>
          <select
            id="remoteType"
            value={remoteType}
            onChange={(e) => setRemoteType(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
          >
            <option value="">Any</option>
            <option value="full">Fully Remote</option>
            <option value="hybrid">Hybrid</option>
            <option value="onsite">On-site</option>
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md flex items-start gap-2">
            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <p className="text-green-700 text-sm">Preferences saved successfully!</p>
          </div>
        )}

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </form>
    </div>
  )
}
