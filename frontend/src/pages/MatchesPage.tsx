import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MatchCard } from '../components/MatchCard'
import { fetchMatches, refreshMatches } from '../api/matches'
import type { MatchFilters } from '../types'

export function MatchesPage() {
  const queryClient = useQueryClient()
  const [minScore, setMinScore] = useState<number>(60)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  // Memoize filters
  const filters = useMemo<MatchFilters>(() => ({
    min_score: minScore,
    status: statusFilter || undefined,
    limit,
    offset,
  }), [minScore, statusFilter, limit, offset])

  // Fetch matches
  const { data, isLoading, error } = useQuery({
    queryKey: ['matches', filters],
    queryFn: () => fetchMatches(filters),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  const matches = data?.matches ?? []
  const total = data?.total ?? 0

  // Mutation for refreshing matches
  const refreshMutation = useMutation({
    mutationFn: refreshMatches,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
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
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Matches'}
        </button>
      </div>

      {/* Success Message */}
      {refreshMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
          <p className="font-medium">Matches refreshed!</p>
          <p className="text-sm">
            Created: {refreshMutation.data.matches_created}, Updated: {refreshMutation.data.matches_updated}
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Min Score Filter */}
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="minScore" className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Match Score
            </label>
            <select
              id="minScore"
              value={minScore}
              onChange={(e) => {
                setMinScore(Number(e.target.value))
                setOffset(0)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value={0}>All Matches (0%+)</option>
              <option value={60}>Fair Matches (60%+)</option>
              <option value={70}>Good Matches (70%+)</option>
              <option value={85}>Excellent Matches (85%+)</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex-1 min-w-[200px]">
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
          {(minScore !== 60 || statusFilter) && (
            <button
              onClick={() => {
                setMinScore(60)
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
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">Loading your matches...</p>
        </div>
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
              : 'Try adjusting your filters or click "Refresh Matches" to find new opportunities.'}
          </p>
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Matches'}
          </button>
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
