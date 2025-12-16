import { memo, useMemo } from 'react'
import type { Job } from '../types'

interface JobCardProps {
  job: Job
}

// Move utility functions outside component to avoid recreating them
const formatSalary = (min: number | null, max: number | null, currency: string) => {
  if (!min && !max) return null
  if (min && max) {
    return `${currency} ${min.toLocaleString()} - ${max.toLocaleString()}`
  }
  if (min) return `${currency} ${min.toLocaleString()}+`
  return `Up to ${currency} ${max?.toLocaleString()}`
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return null
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString()
}

// Memoize component to prevent unnecessary re-renders
export const JobCard = memo(function JobCard({ job }: JobCardProps) {
  const salary = useMemo(
    () => formatSalary(job.salary_min, job.salary_max, job.salary_currency),
    [job.salary_min, job.salary_max, job.salary_currency]
  )
  const postedDate = useMemo(() => formatDate(job.posted_at), [job.posted_at])

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-indigo-600"
            >
              {job.title}
            </a>
          </h3>
          <p className="text-gray-600 font-medium">{job.company}</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
          {job.source}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 mb-3 text-sm text-gray-600">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {job.location}
        </span>

        {job.remote_type && (
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            {job.remote_type === 'full' ? 'Remote' : job.remote_type}
          </span>
        )}

        {job.job_type && (
          <span className="capitalize">{job.job_type}</span>
        )}

        {salary && (
          <span className="font-medium text-green-700">{salary}</span>
        )}

        {postedDate && (
          <span className="ml-auto text-gray-500">{postedDate}</span>
        )}
      </div>

      <p className="text-gray-700 text-sm mb-3 line-clamp-3">
        {job.description.replace(/<[^>]*>/g, '')}
      </p>

      {job.tags && job.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {job.tags.slice(0, 8).map((tag, idx) => (
            <span
              key={idx}
              className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
          {job.tags.length > 8 && (
            <span className="text-xs text-gray-500">+{job.tags.length - 8} more</span>
          )}
        </div>
      )}
    </div>
  )
})
