import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { JobCard } from '../components/JobCard'
import { fetchJobs, refreshJobs } from '../api/jobs'
import type { JobFilters } from '../types'

export function JobsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)

  // Memoize filters to prevent unnecessary re-renders
  const filters = useMemo<JobFilters>(() => ({
    limit,
    offset,
    search: search || undefined,
  }), [limit, offset, search])

  // Use React Query for data fetching with caching
  const { data, isLoading } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  const jobs = data?.jobs ?? []
  const total = data?.total ?? 0

  // Mutation for refreshing jobs (triggers scraper)
  const refreshMutation = useMutation({
    mutationFn: refreshJobs,
    onSuccess: () => {
      // Wait 3 seconds for scraper to complete, then refetch
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['jobs'] })
      }, 3000)
    },
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setOffset(0) // Reset to first page on new search
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="text-gray-600 mt-1">{total} remote jobs available</p>
        </div>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Jobs'}
        </button>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search jobs by title, company, or description..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <button
          type="submit"
          className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700"
        >
          Search
        </button>
        {filters.search && (
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setOffset(0)
            }}
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
          >
            Clear
          </button>
        )}
      </form>

      {isLoading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">Loading jobs...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">
            No jobs found. Click "Refresh Jobs" to scrape latest jobs.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  )
}
