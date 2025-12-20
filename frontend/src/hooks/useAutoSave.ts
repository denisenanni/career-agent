import { useState, useEffect, useRef, useCallback } from 'react'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutoSaveOptions<T> {
  data: T
  onSave: (data: T) => Promise<void>
  debounceMs?: number
  enabled?: boolean
}

interface UseAutoSaveReturn {
  status: SaveStatus
  error: string | null
  save: () => Promise<void>
}

/**
 * Hook for auto-saving data with debounce
 *
 * @param data - The data to save (changes trigger auto-save)
 * @param onSave - Async function to save the data
 * @param debounceMs - Delay before saving (default 1500ms)
 * @param enabled - Whether auto-save is enabled (default true)
 */
export function useAutoSave<T>({
  data,
  onSave,
  debounceMs = 1500,
  enabled = true,
}: UseAutoSaveOptions<T>): UseAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  // Track if this is the initial render
  const isInitialMount = useRef(true)
  // Track the latest data for saving
  const dataRef = useRef(data)
  // Track the timeout for debouncing
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Track if a save is in progress
  const isSavingRef = useRef(false)
  // Track if we need to save again after current save completes
  const pendingSaveRef = useRef(false)

  // Update dataRef when data changes
  useEffect(() => {
    dataRef.current = data
  }, [data])

  const performSave = useCallback(async () => {
    if (isSavingRef.current) {
      pendingSaveRef.current = true
      return
    }

    isSavingRef.current = true
    setStatus('saving')
    setError(null)

    try {
      await onSave(dataRef.current)
      setStatus('saved')

      // Reset to idle after showing "saved" for a moment
      setTimeout(() => {
        setStatus((current) => current === 'saved' ? 'idle' : current)
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
      setStatus('error')
    } finally {
      isSavingRef.current = false

      // If there's a pending save, do it now
      if (pendingSaveRef.current) {
        pendingSaveRef.current = false
        performSave()
      }
    }
  }, [onSave])

  // Debounced save on data change
  useEffect(() => {
    // Skip the initial mount
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }

    if (!enabled) return

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Set new timeout for debounced save
    timeoutRef.current = setTimeout(() => {
      performSave()
    }, debounceMs)

    // Cleanup on unmount or when dependencies change
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [data, debounceMs, enabled, performSave])

  // Manual save function (for immediate save if needed)
  const save = useCallback(async () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    await performSave()
  }, [performSave])

  return { status, error, save }
}
