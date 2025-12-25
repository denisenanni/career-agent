import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { fetchSkillInsights, refreshSkillInsights } from '../api/insights'

export function InsightsPage() {
  const queryClient = useQueryClient()

  // Fetch skill insights
  const { data, isLoading, error } = useQuery({
    queryKey: ['skillInsights'],
    queryFn: () => fetchSkillInsights(),
    staleTime: 1000 * 60 * 30, // Cache for 30 minutes
    retry: false,
  })

  // Mutation for refreshing insights
  const refreshMutation = useMutation({
    mutationFn: refreshSkillInsights,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skillInsights'] })
    },
  })

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Career Insights</h1>
          <p className="text-gray-600 mt-1">
            Market analysis and skill recommendations based on {data?.jobs_analyzed || 0} jobs
          </p>
        </div>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Analysis'}
        </button>
      </div>

      {/* Success Message */}
      {refreshMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
          <p className="font-medium">Analysis refreshed!</p>
          <p className="text-sm">Analyzed {refreshMutation.data.jobs_analyzed} jobs in the market</p>
        </div>
      )}

      {/* Skills Required Warning */}
      {data?.requires_setup === 'skills' && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md">
          <p className="font-medium">CV required for insights</p>
          <p className="text-sm">
            Please upload your CV on the{' '}
            <a href="/profile" className="underline font-medium hover:text-yellow-900">
              Profile page
            </a>{' '}
            to extract your skills and get personalized career insights.
          </p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          <p className="font-medium">Error loading insights</p>
          <p className="text-sm">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <LoadingSpinner size="lg" text="Analyzing market data..." />
      ) : !data || data.requires_setup ? (
        /* Empty/Setup Required State */
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
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No insights available</h3>
          <p className="text-gray-500 mb-4">
            Upload your CV to extract skills and get personalized career insights and recommendations.
          </p>
        </div>
      ) : (
        <>
          {/* Skill Recommendations */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Recommended Skills to Learn</h2>

            {/* Show detected category and note */}
            {data.category_label && (
              <div className="mb-4 flex items-center gap-2">
                <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                  {data.category_label}
                </span>
                {data.note && (
                  <p className="text-sm text-gray-500">{data.note}</p>
                )}
              </div>
            )}

            {!data.category_label && data.note && (
              <p className="text-gray-500 mb-4 text-sm">{data.note}</p>
            )}

            {data.recommendations.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-lg">
                <p className="text-gray-600 font-medium">No recommendations available</p>
                <p className="text-gray-500 text-sm mt-1">
                  {data.user_skills.length === 0
                    ? 'Add skills to your profile to get personalized recommendations.'
                    : 'We couldn\'t find skills related to your current expertise. Try adding more skills to your profile.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`border-2 ${getPriorityColor(rec.priority)} rounded-lg p-4`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{rec.skill}</h3>
                        <p className="text-sm text-gray-700 mt-1">{rec.reason}</p>
                      </div>
                      <div className="flex flex-col gap-1 ml-4">
                        <span className={`text-xs px-2 py-1 rounded font-medium ${getPriorityColor(rec.priority)}`}>
                          {rec.priority.toUpperCase()} PRIORITY
                        </span>
                        <span className={`text-xs px-2 py-1 rounded font-medium ${getEffortColor(rec.learning_effort)}`}>
                          {rec.learning_effort.toUpperCase()} EFFORT
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-600 mt-2">
                      <span>
                        <strong>In {rec.frequency.toFixed(1)}%</strong> of jobs
                      </span>
                      {rec.salary_impact && (
                        <span>
                          <strong>Avg Salary:</strong> ${rec.salary_impact.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Your Skills */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">Your Current Skills</h2>
              {data.category_label && (
                <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                  {data.category_label}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {data.user_skills.length === 0 ? (
                <p className="text-gray-500">No skills added yet</p>
              ) : (
                data.user_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm font-medium border border-green-200"
                  >
                    {skill}
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Skill Gaps */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Skill Gaps to Address</h2>
            <p className="text-gray-600 mb-4">
              These in-demand skills appear frequently in job postings but aren't in your profile yet:
            </p>
            <div className="flex flex-wrap gap-2">
              {data.skill_gaps.length === 0 ? (
                <p className="text-gray-500">No major skill gaps identified</p>
              ) : (
                data.skill_gaps.slice(0, 20).map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-sm font-medium border border-orange-200"
                  >
                    {skill}
                  </span>
                ))
              )}
              {data.skill_gaps.length > 20 && (
                <span className="px-3 py-1 text-gray-500 text-sm">
                  +{data.skill_gaps.length - 20} more
                </span>
              )}
            </div>
          </div>

          {/* Market Overview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Market Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-900">{data.jobs_analyzed}</div>
                <div className="text-sm text-blue-700">Jobs Analyzed</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-900">{data.user_skills.length}</div>
                <div className="text-sm text-green-700">Your Skills</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-900">{data.skill_gaps.length}</div>
                <div className="text-sm text-orange-700">Skill Gaps</div>
              </div>
            </div>

            <h3 className="font-semibold text-gray-900 mb-2">Top 10 Most In-Demand Skills</h3>
            <div className="space-y-2">
              {Object.entries(data.market_skills)
                .sort((a, b) => b[1].frequency - a[1].frequency)
                .slice(0, 10)
                .map(([skill, stats], idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-medium text-gray-900">{skill}</span>
                        <span className="text-sm text-gray-600">
                          {stats.frequency.toFixed(1)}% of jobs
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${Math.min(stats.frequency * 2, 100)}%` }}
                        />
                      </div>
                    </div>
                    {stats.avg_salary && (
                      <div className="text-sm text-green-700 font-medium min-w-[100px] text-right">
                        ${(stats.avg_salary / 1000).toFixed(0)}k avg
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>

          {/* Analysis Date */}
          <div className="text-center text-sm text-gray-500">
            Last updated: {new Date(data.analysis_date).toLocaleString()}
          </div>
        </>
      )}
    </div>
  )
}
