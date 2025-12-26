import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { JobCard } from '../components/JobCard'
import { SkeletonList } from '../components/SkeletonCard'
import { Pagination } from '../components/Pagination'
import { SkillsFilter } from '../components/SkillsFilter'
import { fetchJobs, refreshJobs } from '../api/jobs'
import { useAuth } from '../contexts/AuthContext'
import type { JobFilters } from '../types'

export function JobsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()

  // Initialize state from URL params
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [selectedSkills, setSelectedSkills] = useState<string[]>(
    searchParams.get('skills')?.split(',').filter(Boolean) || []
  )
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10))
  const perPage = 20

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (selectedSkills.length > 0) params.set('skills', selectedSkills.join(','))
    if (page > 1) params.set('page', String(page))
    setSearchParams(params, { replace: true })
  }, [search, selectedSkills, page, setSearchParams])

  // Memoize filters to prevent unnecessary re-renders
  const filters = useMemo<JobFilters>(() => ({
    page,
    per_page: perPage,
    search: search || undefined,
    skills: selectedSkills.length > 0 ? selectedSkills.join(',') : undefined,
  }), [page, perPage, search, selectedSkills])

  // Use React Query for data fetching with caching
  const { data, isLoading } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  })

  const jobs = data?.jobs ?? []
  const pagination = data?.pagination
  const total = pagination?.total ?? 0
  const totalPages = pagination?.total_pages ?? 0
  const hasNext = pagination?.has_next ?? false
  const hasPrev = pagination?.has_prev ?? false

  // Mutation for refreshing jobs (triggers scraper) - admin only
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
    setPage(1) // Reset to first page on new search
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="text-gray-600 mt-1">{total} remote jobs available</p>
        </div>
        {user?.is_admin && (
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Jobs'}
          </button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
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
          {(filters.search || filters.skills) && (
            <button
              type="button"
              onClick={() => {
                setSearch('')
                setSelectedSkills([])
                setPage(1)
              }}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
            >
              Clear
            </button>
          )}
        </form>

        {/* Skills Filter */}
        <SkillsFilter
          selected={selectedSkills}
          onChange={(skills) => {
            setSelectedSkills(skills)
            setPage(1) // Reset to first page when filter changes
          }}
        />
      </div>

      {/* No Jobs Warning */}
      {!isLoading && jobs.length === 0 && !filters.search && !filters.skills && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md">
          <p className="font-medium">No jobs available</p>
          <p className="text-sm">
            Jobs are automatically refreshed daily. Check back soon for new listings.
          </p>
        </div>
      )}

      {isLoading ? (
        <SkeletonList count={5} />
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">
            {filters.search || filters.skills
              ? 'No jobs match your search or filters.'
              : 'No jobs in database yet.'}
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            hasNext={hasNext}
            hasPrev={hasPrev}
          />
        </>
      )}
    </div>
  )
}
