import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { generateCoverLetter, generateCVHighlights, regenerateContent } from '../api/matches'
import { LoadingSpinner } from './LoadingSpinner'
import type { CoverLetterResponse, CVHighlightsResponse } from '../types'

interface ApplicationMaterialsModalProps {
  matchId: number
  jobTitle: string
  company: string
  onClose: () => void
}

type Tab = 'cover-letter' | 'highlights'

export function ApplicationMaterialsModal({
  matchId,
  jobTitle,
  company,
  onClose,
}: ApplicationMaterialsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('cover-letter')
  const [coverLetterData, setCoverLetterData] = useState<CoverLetterResponse | null>(null)
  const [highlightsData, setHighlightsData] = useState<CVHighlightsResponse | null>(null)
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false)

  // Generate cover letter mutation
  const coverLetterMutation = useMutation({
    mutationFn: () => generateCoverLetter(matchId),
    onSuccess: (data) => {
      setCoverLetterData(data)
    },
  })

  // Generate highlights mutation
  const highlightsMutation = useMutation({
    mutationFn: () => generateCVHighlights(matchId),
    onSuccess: (data) => {
      setHighlightsData(data)
    },
  })

  // Regenerate mutation
  const regenerateMutation = useMutation({
    mutationFn: () => regenerateContent(matchId),
    onSuccess: () => {
      // Clear existing data and regenerate
      setCoverLetterData(null)
      setHighlightsData(null)
      setShowRegenerateConfirm(false)
      // Trigger both generations
      coverLetterMutation.mutate()
      highlightsMutation.mutate()
    },
  })

  // Auto-generate on mount
  useEffect(() => {
    coverLetterMutation.mutate()
    highlightsMutation.mutate()
  }, [])

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // Could add a toast notification here
  }

  const downloadAsText = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatHighlights = () => {
    if (!highlightsData) return ''
    return highlightsData.highlights.map((h, i) => `${i + 1}. ${h}`).join('\n\n')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Application Materials</h2>
            <p className="text-sm text-gray-600 mt-1">
              {jobTitle} at {company}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('cover-letter')}
              className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'cover-letter'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Cover Letter
              {coverLetterData?.cached && (
                <span className="ml-2 text-xs">⚡ Cached</span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('highlights')}
              className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'highlights'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              CV Highlights
              {highlightsData?.cached && (
                <span className="ml-2 text-xs">⚡ Cached</span>
              )}
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {activeTab === 'cover-letter' && (
            <div>
              {coverLetterMutation.isPending && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <LoadingSpinner size="lg" />
                    <p className="text-gray-600 mt-4">Generating cover letter...</p>
                    <p className="text-sm text-gray-500 mt-1">Using Claude Sonnet 4.5</p>
                  </div>
                </div>
              )}

              {coverLetterMutation.isError && (
                <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
                  Failed to generate cover letter. Please try again.
                </div>
              )}

              {coverLetterData && (
                <div>
                  <textarea
                    value={coverLetterData.cover_letter}
                    readOnly
                    className="w-full h-96 p-4 border border-gray-300 rounded font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <div className="mt-2 text-xs text-gray-500">
                    Generated at {new Date(coverLetterData.generated_at).toLocaleString()}
                    {coverLetterData.cached && ' • Retrieved from cache (instant!)'}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'highlights' && (
            <div>
              {highlightsMutation.isPending && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <LoadingSpinner size="lg" />
                    <p className="text-gray-600 mt-4">Generating CV highlights...</p>
                    <p className="text-sm text-gray-500 mt-1">Using Claude Haiku</p>
                  </div>
                </div>
              )}

              {highlightsMutation.isError && (
                <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
                  Failed to generate CV highlights. Please try again.
                </div>
              )}

              {highlightsData && (
                <div>
                  <div className="space-y-4 mb-4">
                    {highlightsData.highlights.map((highlight, idx) => (
                      <div key={idx} className="p-4 bg-gray-50 rounded border border-gray-200">
                        <div className="flex items-start gap-3">
                          <span className="font-bold text-indigo-600 text-lg">{idx + 1}.</span>
                          <p className="text-gray-800 flex-1">{highlight}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Generated at {new Date(highlightsData.generated_at).toLocaleString()}
                    {highlightsData.cached && ' • Retrieved from cache (instant!)'}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-gray-200 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div>
            {!showRegenerateConfirm && (
              <button
                onClick={() => setShowRegenerateConfirm(true)}
                disabled={regenerateMutation.isPending}
                className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
              >
                🔄 Regenerate
              </button>
            )}
            {showRegenerateConfirm && (
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <span className="text-sm text-gray-700">Regenerate all content?</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => regenerateMutation.mutate()}
                    disabled={regenerateMutation.isPending}
                    className="text-sm px-3 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 disabled:opacity-50"
                  >
                    {regenerateMutation.isPending ? 'Regenerating...' : 'Yes'}
                  </button>
                  <button
                    onClick={() => setShowRegenerateConfirm(false)}
                    className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2 flex-wrap">
            {activeTab === 'cover-letter' && coverLetterData && (
              <>
                <button
                  onClick={() => copyToClipboard(coverLetterData.cover_letter)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm font-medium"
                >
                  📋 Copy
                </button>
                <button
                  onClick={() => downloadAsText(
                    coverLetterData.cover_letter,
                    `cover-letter-${company.toLowerCase().replace(/\s+/g, '-')}.txt`
                  )}
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium"
                >
                  ⬇ Download
                </button>
              </>
            )}

            {activeTab === 'highlights' && highlightsData && (
              <>
                <button
                  onClick={() => copyToClipboard(formatHighlights())}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm font-medium"
                >
                  📋 Copy
                </button>
                <button
                  onClick={() => downloadAsText(
                    formatHighlights(),
                    `cv-highlights-${company.toLowerCase().replace(/\s+/g, '-')}.txt`
                  )}
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium"
                >
                  ⬇ Download
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
