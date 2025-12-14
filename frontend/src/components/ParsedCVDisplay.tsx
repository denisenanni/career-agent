import { useEffect, useState } from 'react'
import { User, Briefcase, GraduationCap, Mail, Phone, FileText } from 'lucide-react'
import { getParsedCV } from '../api/profile'
import type { ParsedCV } from '../types'

export function ParsedCVDisplay() {
  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadParsedCV()
  }, [])

  async function loadParsedCV() {
    try {
      const data = await getParsedCV()
      setParsedCV(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load parsed CV')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    )
  }

  if (error || !parsedCV) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p>{error || 'No CV data available'}</p>
          <p className="text-sm mt-1">Upload a CV to see parsed information</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Parsed CV Data</h2>
      </div>

      {/* Contact Info */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="w-5 h-5 text-gray-400" />
          <h3 className="font-semibold text-gray-900">{parsedCV.name}</h3>
        </div>
        <div className="ml-7 space-y-1 text-sm text-gray-600">
          {parsedCV.email && (
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              <span>{parsedCV.email}</span>
            </div>
          )}
          {parsedCV.phone && (
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4" />
              <span>{parsedCV.phone}</span>
            </div>
          )}
        </div>
      </div>

      {/* Summary */}
      {parsedCV.summary && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
          <p className="text-sm text-gray-600">{parsedCV.summary}</p>
        </div>
      )}

      {/* Skills */}
      {parsedCV.skills.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Skills</h3>
          <div className="flex flex-wrap gap-2">
            {parsedCV.skills.map((skill, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Experience */}
      {parsedCV.experience.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Briefcase className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Experience ({parsedCV.years_of_experience} years)</h3>
          </div>
          <div className="space-y-4 ml-7">
            {parsedCV.experience.map((exp, index) => (
              <div key={index} className="border-l-2 border-gray-200 pl-4">
                <h4 className="font-medium text-gray-900">{exp.title}</h4>
                <p className="text-sm text-gray-600">{exp.company}</p>
                <p className="text-xs text-gray-500 mb-1">
                  {exp.start_date} - {exp.end_date || 'Present'}
                </p>
                <p className="text-sm text-gray-600 whitespace-pre-line">{exp.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {parsedCV.education.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <GraduationCap className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">Education</h3>
          </div>
          <div className="space-y-3 ml-7">
            {parsedCV.education.map((edu, index) => (
              <div key={index}>
                <h4 className="font-medium text-gray-900">{edu.degree}</h4>
                <p className="text-sm text-gray-600">{edu.institution}</p>
                {edu.field && <p className="text-sm text-gray-600">{edu.field}</p>}
                {edu.end_date && <p className="text-xs text-gray-500">{edu.end_date}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
