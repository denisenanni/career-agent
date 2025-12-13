import { useState, useEffect } from 'react'
import { JobCard } from '../components/JobCard'
import { fetchJobs, refreshJobs } from '../api/jobs'
import type { Job, JobFilters } from '../types'

export function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filters, setFilters] = useState<JobFilters>({ limit: 50 })
  const [search, setSearch] = useState('')

  const loadJobs = async () => {
    try {
      setLoading(true)
      const response = await fetchJobs(filters)
      setJobs(response.jobs)
      setTotal(response.total)
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [filters])

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await refreshJobs()
      setTimeout(() => {
        loadJobs()
      }, 3000)
    } catch (error) {
      console.error('Failed to refresh jobs:', error)
    } finally {
      setRefreshing(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters({ ...filters, search, offset: 0 })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="text-gray-600 mt-1">{total} remote jobs available</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Jobs'}
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
              setFilters({ ...filters, search: undefined, offset: 0 })
            }}
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
          >
            Clear
          </button>
        )}
      </form>

      {loading ? (
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
