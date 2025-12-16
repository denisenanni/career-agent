import { memo, useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Match } from '../types'
import { updateMatchStatus } from '../api/matches'

interface MatchCardProps {
  match: Match
}

const formatSalary = (min: number | null, max: number | null) => {
  if (!min && !max) return null
  if (min && max) {
    return `$${min.toLocaleString()} - $${max.toLocaleString()}`
  }
  if (min) return `$${min.toLocaleString()}+`
  return `Up to $${max?.toLocaleString()}`
}

const getScoreColor = (score: number) => {
  if (score >= 85) return 'text-green-700 bg-green-50 border-green-200'
  if (score >= 70) return 'text-blue-700 bg-blue-50 border-blue-200'
  if (score >= 60) return 'text-yellow-700 bg-yellow-50 border-yellow-200'
  return 'text-gray-700 bg-gray-50 border-gray-200'
}

const getScoreLabel = (score: number) => {
  if (score >= 85) return 'Excellent Match'
  if (score >= 70) return 'Good Match'
  if (score >= 60) return 'Fair Match'
  return 'Low Match'
}

export const MatchCard = memo(function MatchCard({ match }: MatchCardProps) {
  const queryClient = useQueryClient()
  const [showDetails, setShowDetails] = useState(false)
  const salary = useMemo(() => formatSalary(match.job_salary_min, match.job_salary_max), [match.job_salary_min, match.job_salary_max])
  const scoreColor = getScoreColor(match.score)

  const updateStatusMutation = useMutation({
    mutationFn: (status: string) => updateMatchStatus(match.id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })

  return (
    <div className={`bg-white rounded-lg shadow-sm border-2 ${scoreColor.includes('green') ? 'border-green-200' : 'border-gray-200'} p-6 hover:shadow-md transition-shadow`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            <a
              href={match.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-indigo-600"
            >
              {match.job_title}
            </a>
          </h3>
          <p className="text-gray-600 font-medium">{match.job_company}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className={`px-3 py-1 rounded-full font-bold text-lg ${scoreColor} border`}>
            {match.score}%
          </div>
          <span className="text-xs text-gray-600">{getScoreLabel(match.score)}</span>
        </div>
      </div>

      {/* Job Details */}
      <div className="flex flex-wrap gap-2 mb-3 text-sm text-gray-600">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {match.job_location}
        </span>

        {match.job_remote_type && (
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            {match.job_remote_type === 'full' ? 'Remote' : match.job_remote_type}
          </span>
        )}

        {salary && (
          <span className="font-medium text-green-700">{salary}</span>
        )}
      </div>

      {/* Match Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-3 text-xs">
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-900">{match.reasoning.skill_score}%</div>
          <div className="text-gray-600">Skills</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-900">{match.reasoning.work_type_score}%</div>
          <div className="text-gray-600">Work Type</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-900">{match.reasoning.location_score}%</div>
          <div className="text-gray-600">Location</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-900">{match.reasoning.salary_score}%</div>
          <div className="text-gray-600">Salary</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <div className="font-semibold text-gray-900">{match.reasoning.experience_score}%</div>
          <div className="text-gray-600">Experience</div>
        </div>
      </div>

      {/* Matching Skills */}
      {match.reasoning.matching_skills.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-700 mb-1">Your Matching Skills:</p>
          <div className="flex flex-wrap gap-1">
            {match.reasoning.matching_skills.slice(0, 10).map((skill, idx) => (
              <span
                key={idx}
                className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded border border-green-200"
              >
                ✓ {skill}
              </span>
            ))}
            {match.reasoning.matching_skills.length > 10 && (
              <span className="text-xs text-gray-500">+{match.reasoning.matching_skills.length - 10} more</span>
            )}
          </div>
        </div>
      )}

      {/* Missing Skills */}
      {match.reasoning.missing_skills.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-700 mb-1">Skills to Develop:</p>
          <div className="flex flex-wrap gap-1">
            {match.reasoning.missing_skills.slice(0, 8).map((skill, idx) => (
              <span
                key={idx}
                className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200"
              >
                ✗ {skill}
              </span>
            ))}
            {match.reasoning.missing_skills.length > 8 && (
              <span className="text-xs text-gray-500">+{match.reasoning.missing_skills.length - 8} more</span>
            )}
          </div>
        </div>
      )}

      {/* Toggle Details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-sm text-indigo-600 hover:text-indigo-800 mb-2"
      >
        {showDetails ? '▼ Hide Details' : '▶ Show Details'}
      </button>

      {/* Detailed Breakdown (collapsible) */}
      {showDetails && (
        <div className="bg-gray-50 rounded p-3 mb-3 text-xs space-y-2">
          <div>
            <span className="font-semibold">Analysis: </span>
            <span className="text-gray-700">{match.analysis}</span>
          </div>
          <div>
            <span className="font-semibold">Matching Algorithm Weights: </span>
            <span className="text-gray-700">
              Skills: {(match.reasoning.weights.skills * 100).toFixed(0)}%,
              Work Type: {(match.reasoning.weights.work_type * 100).toFixed(0)}%,
              Location: {(match.reasoning.weights.location * 100).toFixed(0)}%,
              Salary: {(match.reasoning.weights.salary * 100).toFixed(0)}%,
              Experience: {(match.reasoning.weights.experience * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 mt-3 pt-3 border-t border-gray-200">
        <button
          onClick={() => updateStatusMutation.mutate('interested')}
          disabled={updateStatusMutation.isPending || match.status === 'interested'}
          className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-colors ${
            match.status === 'interested'
              ? 'bg-blue-100 text-blue-700 cursor-default'
              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
          }`}
        >
          {match.status === 'interested' ? '✓ Interested' : 'Mark Interested'}
        </button>
        <button
          onClick={() => updateStatusMutation.mutate('applied')}
          disabled={updateStatusMutation.isPending || match.status === 'applied'}
          className={`flex-1 py-2 px-3 rounded text-sm font-medium transition-colors ${
            match.status === 'applied'
              ? 'bg-green-100 text-green-700 cursor-default'
              : 'bg-green-50 text-green-700 hover:bg-green-100'
          }`}
        >
          {match.status === 'applied' ? '✓ Applied' : 'Mark Applied'}
        </button>
        <button
          onClick={() => updateStatusMutation.mutate('hidden')}
          disabled={updateStatusMutation.isPending}
          className="py-2 px-3 rounded text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
        >
          Hide
        </button>
      </div>
    </div>
  )
})
