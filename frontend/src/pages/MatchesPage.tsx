import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { MatchCard } from '../components/MatchCard'
import { SkeletonList } from '../components/SkeletonCard'
import { fetchMatches, refreshMatches, getRefreshStatus } from '../api/matches'
import { getProfile } from '../api/profile'
import { useAuth } from '../contexts/AuthContext'
import type { MatchFilters, RefreshStatusResponse } from '../types'

export function MatchesPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [scoreRange, setScoreRange] = useState<string>('60+')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Memoize filters with exclusive score ranges
  const filters = useMemo<MatchFilters>(() => {
    let min_score: number | undefined
    let max_score: number | undefined

    switch (scoreRange) {
      case 'all':
        min_score = 0
        break
      case '60-69':
        min_score = 60
        max_score = 69
        break
      case '70-84':
        min_score = 70
        max_score = 84
        break
      case '85+':
        min_score = 85
        break
      case '60+':
      default:
        min_score = 60
        break
    }

    return {
      min_score,
      max_score,
      status: statusFilter || undefined,
      limit,
      offset,
    }
  }, [scoreRange, statusFilter, limit, offset])

  // Fetch matches
  const { data, isLoading, error } = useQuery({
    queryKey: ['matches', filters],
    queryFn: () => fetchMatches(filters),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  const matches = data?.matches ?? []
  const total = data?.total ?? 0

  // Fetch user profile to check if CV is uploaded
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  const hasCVUploaded = profile?.cv_uploaded_at !== null

  // Stop polling helper
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  // Handle status check
  const checkStatus = useCallback(async () => {
    try {
      const status: RefreshStatusResponse = await getRefreshStatus()

      if (status.status === 'completed') {
        stopPolling()
        setIsRefreshing(false)
        toast.dismiss('refresh-matches')
        queryClient.invalidateQueries({ queryKey: ['matches'] })

        const matchCount = status.result?.matches_created ?? 0
        const updatedCount = status.result?.matches_updated ?? 0
        toast.success(`Found ${matchCount + updatedCount} matches! (${matchCount} new)`)
      } else if (status.status === 'failed') {
        stopPolling()
        setIsRefreshing(false)
        toast.dismiss('refresh-matches')
        toast.error(status.message || 'Match refresh failed')
      }
      // Keep polling if still pending/processing
    } catch {
      stopPolling()
      setIsRefreshing(false)
      toast.dismiss('refresh-matches')
      toast.error('Failed to check refresh status')
    }
  }, [queryClient, stopPolling])

  // Start polling when refresh begins
  const startPolling = useCallback(() => {
    stopPolling() // Clear any existing polling
    pollingRef.current = setInterval(checkStatus, 2500) // Poll every 2.5 seconds
  }, [checkStatus, stopPolling])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  // Mutation for refreshing matches
  const refreshMutation = useMutation({
    mutationFn: refreshMatches,
    onSuccess: (data) => {
      if (data.status === 'processing') {
        setIsRefreshing(true)
        startPolling()
        toast.loading('Refreshing matches...', { id: 'refresh-matches' })
      } else if (data.status === 'already_processing') {
        setIsRefreshing(true)
        startPolling()
        toast('Refresh already in progress', { icon: '⏳' })
      }
    },
    onError: () => {
      toast.error('Failed to start match refresh')
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Job Matches</h1>
          <p className="text-gray-600 mt-1">
            {total} {total === 1 ? 'match' : 'matches'} found based on your profile
          </p>
        </div>
        {user?.is_admin && (
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={isRefreshing || refreshMutation.isPending}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh Matches'}
          </button>
        )}
      </div>

      {/* CV Required Warning */}
      {!hasCVUploaded && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md">
          <p className="font-medium">CV required for job matching</p>
          <p className="text-sm">
            Please upload your CV on the{' '}
            <a href="/profile" className="underline font-medium hover:text-yellow-900">
              Profile page
            </a>{' '}
            to get personalized job matches.
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Score Range Filter */}
          <div className="flex-1 min-w-0 sm:min-w-[200px]">
            <label htmlFor="scoreRange" className="block text-sm font-medium text-gray-700 mb-1">
              Match Score Range
            </label>
            <select
              id="scoreRange"
              value={scoreRange}
              onChange={(e) => {
                setScoreRange(e.target.value)
                setOffset(0)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="all">All Matches (0%+)</option>
              <option value="60+">All Good Matches (60%+)</option>
              <option value="60-69">Fair Matches (60-69%)</option>
              <option value="70-84">Good Matches (70-84%)</option>
              <option value="85+">Excellent Matches (85%+)</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex-1 min-w-0 sm:min-w-[200px]">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setOffset(0)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="matched">New Matches</option>
              <option value="interested">Interested</option>
              <option value="applied">Applied</option>
            </select>
          </div>

          {/* Clear Filters */}
          {(scoreRange !== '60+' || statusFilter) && (
            <button
              onClick={() => {
                setScoreRange('60+')
                setStatusFilter('')
                setOffset(0)
              }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          <p className="font-medium">Error loading matches</p>
          <p className="text-sm">{error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <SkeletonList count={3} />
      ) : matches.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No matches found</h3>
          <p className="text-gray-500 mb-4">
            {error
              ? 'Please make sure you have uploaded your CV and added skills to your profile.'
              : 'Matches are generated automatically when new jobs are scraped. Try adjusting your filters or check back later.'}
          </p>
          {user?.is_admin && (
            <button
              onClick={() => refreshMutation.mutate()}
              disabled={isRefreshing || refreshMutation.isPending}
              className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
            >
              {isRefreshing ? 'Refreshing...' : 'Refresh Matches'}
            </button>
          )}
        </div>
      ) : (
        /* Matches List */
        <div className="space-y-4">
          {matches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  )
}
