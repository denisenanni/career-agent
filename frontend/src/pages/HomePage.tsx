import { Link } from 'react-router-dom'
import { Upload, Search, FileText } from 'lucide-react'

export function HomePage() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">
          Your AI-Powered Job Hunt Assistant
        </h1>
        <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your CV, set your preferences, and let us find the perfect job matches for you.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
            <Upload className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">1. Upload CV</h3>
          <p className="mt-2 text-gray-600">
            Upload your CV and we'll extract your skills and experience automatically.
          </p>
          <Link
            to="/profile"
            className="mt-4 inline-flex items-center text-indigo-600 hover:text-indigo-700"
          >
            Go to Profile →
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
            <Search className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">2. Browse Jobs</h3>
          <p className="mt-2 text-gray-600">
            We scrape top job boards and rank jobs based on your profile match.
          </p>
          <Link
            to="/jobs"
            className="mt-4 inline-flex items-center text-indigo-600 hover:text-indigo-700"
          >
            Browse Jobs →
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
            <FileText className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">3. Apply Smart</h3>
          <p className="mt-2 text-gray-600">
            Generate tailored cover letters and CV highlights for each application.
          </p>
          <Link
            to="/matches"
            className="mt-4 inline-flex items-center text-indigo-600 hover:text-indigo-700"
          >
            View Matches →
          </Link>
        </div>
      </div>

      <div className="bg-indigo-50 rounded-lg p-6 mt-8">
        <h2 className="text-lg font-semibold text-indigo-900">Status</h2>
        <p className="mt-2 text-indigo-700">
          🚧 This is a work in progress. Features are being added incrementally.
        </p>
      </div>
    </div>
  )
}
