import { memo } from 'react'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import type { SaveStatus } from '../hooks/useAutoSave'

interface SaveStatusIndicatorProps {
  status: SaveStatus
  error?: string | null
}

export const SaveStatusIndicator = memo(function SaveStatusIndicator({
  status,
  error
}: SaveStatusIndicatorProps) {
  if (status === 'idle') {
    return null
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      {status === 'saving' && (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
          <span className="text-gray-500">Saving...</span>
        </>
      )}
      {status === 'saved' && (
        <>
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="text-green-600">Saved</span>
        </>
      )}
      {status === 'error' && (
        <>
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-red-600">{error || 'Failed to save'}</span>
        </>
      )}
    </div>
  )
})
