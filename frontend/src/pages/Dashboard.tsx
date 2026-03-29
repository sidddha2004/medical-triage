import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { sessionAPI } from '../lib/api'

interface Session {
  id: number
  status: string
  triage_level: string
  created_at: string
  primary_symptoms: string[]
}

export default function Dashboard() {
  const [recentSessions, setRecentSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const logout = useAuthStore((state) => state.logout)

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    loadRecentSessions()
  }, [isAuthenticated, navigate])

  const loadRecentSessions = async () => {
    try {
      const response = await sessionAPI.getSessions()
      setRecentSessions(response.data.results || response.data || [])
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTriageLevelColor = (level: string) => {
    switch (level) {
      case 'emergency': return 'text-red-600 bg-red-100 dark:bg-red-900/30'
      case 'urgent_care': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30'
      case 'gp_visit': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
      case 'self_care': return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30'
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
              <button onClick={handleLogout} className="btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="card mb-6">
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

          {/* Recent Sessions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Recent Assessments
            </h3>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                <p className="text-gray-500 dark:text-gray-400 mt-2">Loading...</p>
              </div>
            ) : recentSessions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  No assessments yet. Start a new assessment to see your results here.
                </p>
                <Link to="/chat" className="text-primary-600 hover:text-primary-500 text-sm mt-2 inline-block">
                  Start Assessment →
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symptoms</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Triage Level</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {recentSessions.slice(0, 5).map((session) => (
                      <tr key={session.id}>
                        <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">
                          {new Date(session.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300">
                          {session.primary_symptoms?.slice(0, 3).join(', ') || 'N/A'}
                          {session.primary_symptoms?.length > 3 && '...'}
                        </td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTriageLevelColor(session.triage_level || 'self_care')}`}>
                            {(session.triage_level || 'N/A').replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300">
                          {session.status}
                        </td>
                        <td className="px-4 py-2">
                          <Link
                            to={`/results?session=${session.id}`}
                            className="text-primary-600 hover:text-primary-500 text-sm"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
