import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { uploadCV } from '../api/profile'
import { LoadingSpinner } from './LoadingSpinner'
import type { CVUploadResponse } from '../types'

interface CVUploadProps {
  onUploadSuccess: (response: CVUploadResponse) => void
}

export function CVUpload({ onUploadSuccess }: CVUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<CVUploadResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['.pdf', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!validTypes.includes(fileExtension)) {
      setError('Invalid file type. Please upload PDF, DOCX, or TXT files.')
      return
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setError('File too large. Maximum size is 5MB.')
      return
    }

    setError(null)
    setSuccess(null)
    setUploading(true)

    try {
      const response = await uploadCV(file)
      setSuccess(response)
      onUploadSuccess(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload CV')
    } finally {
      setUploading(false)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload CV</h2>

      <div
        onClick={handleClick}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-indigo-400 transition-colors"
      >
        {uploading ? (
          <LoadingSpinner size="lg" text="Uploading and parsing CV..." />
        ) : success ? (
          <>
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <p className="text-gray-900 font-medium mb-2">{success.filename}</p>
            <p className="text-gray-600 text-sm">{success.message}</p>
          </>
        ) : (
          <>
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">
              Drag and drop your CV here, or click to browse
            </p>
            <p className="text-gray-400 text-sm">
              Supports PDF, DOCX, TXT (max 5MB)
            </p>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt"
          onChange={handleFileSelect}
        />
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {!success && !uploading && (
        <button
          onClick={handleClick}
          className="mt-4 w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
        >
          <FileText className="w-4 h-4" />
          Select File
        </button>
      )}
    </div>
  )
}
