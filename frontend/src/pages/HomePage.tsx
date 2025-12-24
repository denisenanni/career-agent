import { Link } from 'react-router-dom'
import { Upload, Search, FileText, Sparkles, Target, Zap } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export function HomePage() {
  const { user } = useAuth()

  // Logged-out: Hero with value proposition
  if (!user) {
    return (
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="text-center py-12">
          <h1 className="text-5xl font-bold text-gray-900">
            Land Your Dream Job with AI
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
            Stop wasting hours on job applications. Upload your CV once, and let AI match you
            with the perfect opportunities and generate tailored cover letters.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link
              to="/register"
              className="px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Get Started Free
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Value Props */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Target className="w-7 h-7 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Smart Matching</h3>
            <p className="mt-2 text-gray-600">
              AI analyzes your skills and experience to find jobs where you're a strong fit.
            </p>
          </div>
          <div className="text-center">
            <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-7 h-7 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">AI Cover Letters</h3>
            <p className="mt-2 text-gray-600">
              Generate personalized cover letters tailored to each job in seconds.
            </p>
          </div>
          <div className="text-center">
            <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-7 h-7 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Save Hours</h3>
            <p className="mt-2 text-gray-600">
              Stop manually searching job boards. We aggregate and rank opportunities for you.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Logged-in: User flow cards
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">
          Welcome back{user.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}!
        </h1>
        <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
          Continue your job search journey.
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
    </div>
  )
}
