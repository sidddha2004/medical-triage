import { Link } from 'react-router-dom'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Health Triage
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/chat" className="btn-primary">
                New Assessment
              </Link>
              <Link to="/results" className="btn-secondary">
                Results
              </Link>
              <Link to="/history" className="btn-secondary">
                History
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Welcome to Health Triage Assistant
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Get AI-powered symptom assessments and triage recommendations.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card border-l-4 border-primary-500">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Start Assessment
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Chat with our AI about your symptoms
                </p>
                <Link to="/chat" className="text-primary-600 hover:text-primary-500 text-sm mt-2 inline-block">
                  Begin →
                </Link>
              </div>
              <div className="card border-l-4 border-green-500">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  View Results
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  See your latest triage assessments
                </p>
                <Link to="/results" className="text-green-600 hover:text-green-500 text-sm mt-2 inline-block">
                  View →
                </Link>
              </div>
              <div className="card border-l-4 border-purple-500">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  History & Trends
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Track your health over time
                </p>
                <Link to="/history" className="text-purple-600 hover:text-purple-500 text-sm mt-2 inline-block">
                  Explore →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
