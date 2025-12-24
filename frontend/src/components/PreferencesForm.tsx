import { useState, useEffect, useMemo, useCallback } from 'react'
import { Settings } from 'lucide-react'
import { updateProfile } from '../api/profile'
import { useAuth } from '../contexts/AuthContext'
import { useAutoSave } from '../hooks/useAutoSave'
import { SaveStatusIndicator } from './SaveStatusIndicator'
import { CollapsibleSection } from './CollapsibleSection'
import type { UserPreferences } from '../types'

export function PreferencesForm() {
  const { user } = useAuth()

  // Form state
  const [minSalary, setMinSalary] = useState<number | ''>('')
  const [minSalaryError, setMinSalaryError] = useState('')
  const [jobTypes, setJobTypes] = useState<string[]>([])
  const [remoteTypes, setRemoteTypes] = useState<string[]>([])
  const [preferredCountries, setPreferredCountries] = useState<string[]>([])
  const [eligibleRegions, setEligibleRegions] = useState<string[]>([])
  const [needsVisaSponsorship, setNeedsVisaSponsorship] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)

  // Load current preferences
  useEffect(() => {
    if (user?.preferences) {
      setMinSalary(user.preferences.min_salary || '')
      setJobTypes(user.preferences.job_types || [])
      setRemoteTypes(user.preferences.remote_types || [])
      setPreferredCountries(user.preferences.preferred_countries || [])
      setEligibleRegions(user.preferences.eligible_regions || [])
      setNeedsVisaSponsorship(user.preferences.needs_visa_sponsorship || false)
      // Mark as initialized after loading user data
      setIsInitialized(true)
    } else if (user) {
      // User exists but no preferences yet
      setIsInitialized(true)
    }
  }, [user])

  // Build preferences object for auto-save
  const preferences = useMemo((): UserPreferences => {
    const prefs: UserPreferences = {}
    if (minSalary !== '') prefs.min_salary = Number(minSalary)
    if (jobTypes.length > 0) prefs.job_types = jobTypes
    if (remoteTypes.length > 0) prefs.remote_types = remoteTypes
    if (preferredCountries.length > 0) prefs.preferred_countries = preferredCountries
    if (eligibleRegions.length > 0) prefs.eligible_regions = eligibleRegions
    prefs.needs_visa_sponsorship = needsVisaSponsorship
    return prefs
  }, [minSalary, jobTypes, remoteTypes, preferredCountries, eligibleRegions, needsVisaSponsorship])

  // Auto-save hook
  const { status, error } = useAutoSave({
    data: preferences,
    onSave: async (prefs) => {
      await updateProfile({ preferences: prefs })
      // Note: refreshUser() removed - form state is already updated locally
      // and preferences are saved to backend
    },
    debounceMs: 1500,
    enabled: isInitialized, // Only enable after initial load
  })

  // Toggle handlers for checkboxes (memoized to prevent unnecessary re-renders)
  const toggleJobType = useCallback((type: string) => {
    setJobTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }, [])

  const toggleRemoteType = useCallback((type: string) => {
    setRemoteTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }, [])

  const toggleCountry = useCallback((country: string) => {
    setPreferredCountries(prev =>
      prev.includes(country) ? prev.filter(c => c !== country) : [...prev, country]
    )
  }, [])

  const toggleEligibleRegion = useCallback((region: string) => {
    setEligibleRegions(prev =>
      prev.includes(region) ? prev.filter(r => r !== region) : [...prev, region]
    )
  }, [])

  const validateMinSalary = (value: number | '') => {
    if (value !== '' && value < 0) {
      setMinSalaryError('Salary must be a positive number')
      return false
    }
    if (value !== '' && value > 10000000) {
      setMinSalaryError('Salary seems unreasonably high')
      return false
    }
    setMinSalaryError('')
    return true
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900">Job Preferences</h2>
        </div>
        <SaveStatusIndicator status={status} error={error} />
      </div>

      <div className="space-y-4">
        <div>
          <label htmlFor="minSalary" className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Salary (USD/year)
          </label>
          <input
            id="minSalary"
            type="number"
            value={minSalary}
            onChange={(e) => {
              const value = e.target.value ? Number(e.target.value) : ''
              setMinSalary(value)
              if (minSalaryError) validateMinSalary(value)
            }}
            onBlur={(e) => {
              const value = e.target.value ? Number(e.target.value) : ''
              validateMinSalary(value)
            }}
            className={`mt-1 block w-full rounded-md shadow-sm focus:ring-indigo-500 px-3 py-2 border ${
              minSalaryError ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
            }`}
            placeholder="e.g., 120000"
            min="0"
            step="1000"
          />
          {minSalaryError && (
            <p className="mt-1 text-sm text-red-600">{minSalaryError}</p>
          )}
        </div>

        <CollapsibleSection title="Job Types" selectedCount={jobTypes.length}>
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
        </CollapsibleSection>

        <CollapsibleSection title="Remote Work Preference" selectedCount={remoteTypes.length}>
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
        </CollapsibleSection>

        <CollapsibleSection title="Preferred Countries/Locations" selectedCount={preferredCountries.length}>
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
        </CollapsibleSection>

        <CollapsibleSection title="Employment Eligibility" selectedCount={eligibleRegions.length}>
          <div className="space-y-2">
            {[
              { value: 'Worldwide', label: 'Worldwide (no restrictions)' },
              { value: 'US', label: 'United States' },
              { value: 'EU', label: 'European Union' },
              { value: 'UK', label: 'United Kingdom' },
              { value: 'Canada', label: 'Canada' },
              { value: 'Australia', label: 'Australia' },
              { value: 'Asia', label: 'Asia' }
            ].map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={eligibleRegions.includes(value)}
                  onChange={() => toggleEligibleRegion(value)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
          {eligibleRegions.length === 0 && (
            <p className="text-xs text-gray-500 mt-1">No selection = all regions</p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            Jobs restricted to regions you haven't selected will be filtered out
          </p>
        </CollapsibleSection>

        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={needsVisaSponsorship}
              onChange={(e) => setNeedsVisaSponsorship(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
            />
            <span className="text-sm font-medium text-gray-700">
              I need visa sponsorship
            </span>
          </label>
          <p className="text-xs text-gray-500 mt-1 ml-6">
            Jobs that explicitly don't offer visa sponsorship will be filtered out
          </p>
        </div>
      </div>
    </div>
  )
}
