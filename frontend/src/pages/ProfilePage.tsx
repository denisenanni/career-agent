import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { CVUpload } from '../components/CVUpload'
import { ParsedCVDisplay } from '../components/ParsedCVDisplay'
import { PreferencesForm } from '../components/PreferencesForm'
import type { CVUploadResponse } from '../types'

export function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [showParsedCV, setShowParsedCV] = useState(false)
  const [parsedCVRefreshTrigger, setParsedCVRefreshTrigger] = useState(0)

  const handleUploadSuccess = async (_response: CVUploadResponse) => {
    // Refresh user to get updated profile
    await refreshUser()
    // Show parsed CV display
    setShowParsedCV(true)
    // Trigger ParsedCVDisplay to reload
    setParsedCVRefreshTrigger(prev => prev + 1)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
        {user && (
          <div className="text-right">
            <p className="text-sm text-gray-600">Logged in as</p>
            <p className="font-medium text-gray-900">{user.email}</p>
          </div>
        )}
      </div>

      {/* Profile Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Name:</span>
            <span className="ml-2 text-gray-900">{user?.full_name || 'Not set'}</span>
          </div>
          <div>
            <span className="text-gray-600">Experience:</span>
            <span className="ml-2 text-gray-900">
              {user?.experience_years ? `${user.experience_years} years` : 'Not set'}
            </span>
          </div>
          <div className="md:col-span-2">
            <span className="text-gray-600">Skills:</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {user?.skills && user.skills.length > 0 ? (
                user.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {skill}
                  </span>
                ))
              ) : (
                <span className="text-gray-500 text-sm">No skills added yet</span>
              )}
            </div>
          </div>
          {user?.cv_filename && (
            <div className="md:col-span-2">
              <span className="text-gray-600">CV Uploaded:</span>
              <span className="ml-2 text-gray-900">{user.cv_filename}</span>
              <span className="ml-2 text-gray-500 text-xs">
                ({new Date(user.cv_uploaded_at!).toLocaleDateString()})
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* CV Upload */}
        <CVUpload onUploadSuccess={handleUploadSuccess} />

        {/* Preferences Form */}
        <PreferencesForm />
      </div>

      {/* Parsed CV Display */}
      {(showParsedCV || user?.cv_filename) && (
        <ParsedCVDisplay refreshTrigger={parsedCVRefreshTrigger} />
      )}
    </div>
  )
}
