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
  const [jobTypes, setJobTypes] = useState<string[]>([])
  const [remoteTypes, setRemoteTypes] = useState<string[]>([])
  const [preferredCountries, setPreferredCountries] = useState<string[]>([])

  // Load current preferences
  useEffect(() => {
    if (user?.preferences) {
      setMinSalary(user.preferences.min_salary || '')
      setJobTypes(user.preferences.job_types || [])
      setRemoteTypes(user.preferences.remote_types || [])
      setPreferredCountries(user.preferences.preferred_countries || [])
    }
  }, [user])

  // Toggle handlers for checkboxes
  const toggleJobType = (type: string) => {
    setJobTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }

  const toggleRemoteType = (type: string) => {
    setRemoteTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }

  const toggleCountry = (country: string) => {
    setPreferredCountries(prev =>
      prev.includes(country) ? prev.filter(c => c !== country) : [...prev, country]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setSaving(true)

    try {
      // Build preferences object
      const preferences: Record<string, any> = {}

      if (minSalary !== '') preferences.min_salary = Number(minSalary)
      if (jobTypes.length > 0) preferences.job_types = jobTypes
      if (remoteTypes.length > 0) preferences.remote_types = remoteTypes
      if (preferredCountries.length > 0) preferences.preferred_countries = preferredCountries

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
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Types <span className="text-gray-500 text-xs">(select all that apply)</span>
          </label>
          <div className="space-y-2">
            {['permanent', 'contract', 'freelance', 'part-time'].map((type) => (
              <label key={type} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={jobTypes.includes(type)}
                  onChange={() => toggleJobType(type)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
                <span className="text-sm text-gray-700 capitalize">{type === 'part-time' ? 'Part-time' : type}</span>
              </label>
            ))}
          </div>
          {jobTypes.length === 0 && (
            <p className="text-xs text-gray-500 mt-1">No selection = open to all types</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Remote Work Preference <span className="text-gray-500 text-xs">(select all that apply)</span>
          </label>
          <div className="space-y-2">
            {[
              { value: 'full', label: 'Fully Remote' },
              { value: 'hybrid', label: 'Hybrid' },
              { value: 'onsite', label: 'On-site' }
            ].map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={remoteTypes.includes(value)}
                  onChange={() => toggleRemoteType(value)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
          {remoteTypes.length === 0 && (
            <p className="text-xs text-gray-500 mt-1">No selection = open to all types</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Countries/Locations <span className="text-gray-500 text-xs">(select all that apply)</span>
          </label>
          <div className="space-y-2">
            {[
              'Remote',
              'United States',
              'United Kingdom',
              'Canada',
              'Germany',
              'Netherlands',
              'Australia',
              'Singapore',
              'Other Europe',
              'Other Asia'
            ].map((country) => (
              <label key={country} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferredCountries.includes(country)}
                  onChange={() => toggleCountry(country)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
                <span className="text-sm text-gray-700">{country}</span>
              </label>
            ))}
          </div>
          {preferredCountries.length === 0 && (
            <p className="text-xs text-gray-500 mt-1">No selection = open to all locations</p>
          )}
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
