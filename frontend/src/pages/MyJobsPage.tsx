import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Briefcase, Trash2, ExternalLink, MapPin, DollarSign } from 'lucide-react'
import { SkeletonList } from '../components/SkeletonCard'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { getUserJobs, deleteUserJob, parseJobText, createUserJob, type UserJob, type UserJobCreate } from '../api/userJobs'

export function MyJobsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [jobText, setJobText] = useState('')
  const [parsedJob, setParsedJob] = useState<UserJobCreate | null>(null)
  const [parsing, setParsing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch user jobs
  const { data, isLoading } = useQuery({
    queryKey: ['user-jobs'],
    queryFn: getUserJobs,
    staleTime: 1000 * 60 * 5,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteUserJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-jobs'] })
    },
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createUserJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-jobs'] })
      setShowForm(false)
      setJobText('')
      setParsedJob(null)
    },
  })

  const jobs = data?.jobs ?? []
  const total = data?.total ?? 0

  const handleParse = async () => {
    if (!jobText.trim() || jobText.length < 50) {
      setError('Please paste at least 50 characters of job text')
      return
    }

    setError(null)
    setParsing(true)

    try {
      const parsed = await parseJobText(jobText)
      setParsedJob(parsed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse job text')
    } finally {
      setParsing(false)
    }
  }

  const handleSave = async () => {
    if (!parsedJob) return

    try {
      await createMutation.mutateAsync(parsedJob)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save job')
    }
  }

  const handleDelete = async (jobId: number) => {
    if (confirm('Are you sure you want to delete this job?')) {
      try {
        await deleteMutation.mutateAsync(jobId)
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to delete job')
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Jobs</h1>
          <p className="text-gray-600 mt-1">
            {total} {total === 1 ? 'job' : 'jobs'} you've added
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Job
        </button>
      </div>

      {/* Add Job Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add New Job</h2>

          {!parsedJob ? (
            <>
              <div className="mb-4">
                <label htmlFor="jobText" className="block text-sm font-medium text-gray-700 mb-2">
                  Paste Job Posting
                </label>
                <textarea
                  id="jobText"
                  value={jobText}
                  onChange={(e) => setJobText(e.target.value)}
                  placeholder="Paste the full job posting text here (minimum 50 characters)..."
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <p className="text-sm text-gray-500 mt-1">
                  {jobText.length} characters
                </p>
              </div>

              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={handleParse}
                  disabled={parsing || jobText.length < 50}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 flex items-center gap-2"
                >
                  {parsing && <LoadingSpinner size="sm" />}
                  {parsing ? 'Parsing with AI...' : 'Parse Job'}
                </button>
                <button
                  onClick={() => {
                    setShowForm(false)
                    setJobText('')
                    setError(null)
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="space-y-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    value={parsedJob.title}
                    onChange={(e) => setParsedJob({ ...parsedJob, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company
                  </label>
                  <input
                    type="text"
                    value={parsedJob.company || ''}
                    onChange={(e) => setParsedJob({ ...parsedJob, company: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={parsedJob.location || ''}
                    onChange={(e) => setParsedJob({ ...parsedJob, location: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Remote Type
                    </label>
                    <select
                      value={parsedJob.remote_type || ''}
                      onChange={(e) => setParsedJob({ ...parsedJob, remote_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="">Not specified</option>
                      <option value="full">Full Remote</option>
                      <option value="hybrid">Hybrid</option>
                      <option value="onsite">Onsite</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Job Type
                    </label>
                    <select
                      value={parsedJob.job_type || ''}
                      onChange={(e) => setParsedJob({ ...parsedJob, job_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="">Not specified</option>
                      <option value="permanent">Permanent</option>
                      <option value="contract">Contract</option>
                      <option value="part-time">Part-time</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job URL
                  </label>
                  <input
                    type="url"
                    value={parsedJob.url || ''}
                    onChange={(e) => setParsedJob({ ...parsedJob, url: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={parsedJob.description}
                    onChange={(e) => setParsedJob({ ...parsedJob, description: e.target.value })}
                    className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>

              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={handleSave}
                  disabled={createMutation.isPending || !parsedJob.title}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
                >
                  {createMutation.isPending ? 'Saving...' : 'Save Job'}
                </button>
                <button
                  onClick={() => setParsedJob(null)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Back to Edit
                </button>
                <button
                  onClick={() => {
                    setShowForm(false)
                    setJobText('')
                    setParsedJob(null)
                    setError(null)
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <SkeletonList count={2} />
      ) : jobs.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <Briefcase className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs yet</h3>
          <p className="text-gray-500 mb-4">
            Add jobs you've found elsewhere to track and analyze them.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Your First Job
          </button>
        </div>
      ) : (
        /* Jobs List */
        <div className="space-y-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} onDelete={() => handleDelete(job.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function JobCard({ job, onDelete }: { job: UserJob; onDelete: () => void }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{job.title}</h3>
          {job.company && (
            <p className="text-gray-600 mb-2">{job.company}</p>
          )}
        </div>
        <button
          onClick={onDelete}
          className="text-red-600 hover:text-red-800 p-2 rounded-md hover:bg-red-50"
          title="Delete job"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-4">
        {job.location && (
          <div className="flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            {job.location}
          </div>
        )}
        {job.salary_min && job.salary_max && (
          <div className="flex items-center gap-1">
            <DollarSign className="w-4 h-4" />
            {job.salary_currency} {job.salary_min.toLocaleString()} - {job.salary_max.toLocaleString()}
          </div>
        )}
        {job.remote_type && (
          <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium">
            {job.remote_type === 'full' ? 'Remote' : job.remote_type === 'hybrid' ? 'Hybrid' : 'Onsite'}
          </span>
        )}
        {job.job_type && (
          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-xs font-medium">
            {job.job_type}
          </span>
        )}
      </div>

      {job.tags && job.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {job.tags.slice(0, 6).map((tag, idx) => (
            <span key={idx} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs">
              {tag}
            </span>
          ))}
          {job.tags.length > 6 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs">
              +{job.tags.length - 6} more
            </span>
          )}
        </div>
      )}

      <p className="text-gray-700 text-sm line-clamp-3 mb-4">{job.description}</p>

      <div className="flex justify-between items-center">
        <p className="text-xs text-gray-500">
          Added {new Date(job.created_at).toLocaleDateString()}
        </p>
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 text-sm"
          >
            View Posting
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  )
}
