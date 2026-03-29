import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { sessionAPI } from '../lib/api'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

interface Session {
  id: number
  status: string
  triage_level: string
  created_at: string
  primary_symptoms: string[]
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#6366F1', '#14B8A6']

export default function History() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }
    loadHistory()
  }, [isAuthenticated])

  const loadHistory = async () => {
    try {
      const response = await sessionAPI.getSessions()
      const data = response.data.results || response.data || []
      setSessions(data)
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoading(false)
    }
  }

  // Prepare data for triage level distribution
  const triageLevelData = (() => {
    const counts: Record<string, number> = {}
    sessions.forEach(s => {
      const level = s.triage_level || 'unknown'
      counts[level] = (counts[level] || 0) + 1
    })
    return Object.entries(counts).map(([name, value]) => ({
      name: name.replace('_', ' '),
      value
    }))
  })()

  // Prepare data for assessments over time
  const assessmentsOverTime = (() => {
    const byDate: Record<string, number> = {}
    sessions.forEach(s => {
      const date = new Date(s.created_at).toLocaleDateString()
      byDate[date] = (byDate[date] || 0) + 1
    })
    return Object.entries(byDate)
      .map(([date, count]) => ({ date, count }))
      .slice(-7) // Last 7 data points
  })()

  // Top symptoms
  const topSymptoms = (() => {
    const counts: Record<string, number> = {}
    sessions.forEach(s => {
      s.primary_symptoms?.forEach((symptom: string) => {
        counts[symptom] = (counts[symptom] || 0) + 1
      })
    })
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
  })()

  const getTriageLevelColor = (level: string) => {
    switch (level) {
      case 'emergency': return 'text-red-600 bg-red-100 dark:bg-red-900/30'
      case 'urgent_care': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30'
      case 'gp_visit': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
      case 'self_care': return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30'
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Please login to view your history
          </h1>
          <Link to="/login" className="btn-primary">
            Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                History & Trends
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="btn-secondary">
                Back to Dashboard
              </Link>
              <Link to="/chat" className="btn-primary">
                New Assessment
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        {loading ? (
          <div className="card text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 dark:text-gray-400 mt-2">Loading history...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="card text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No assessment history yet. Start your first assessment to track your health trends.
            </p>
            <Link to="/chat" className="btn-primary">
              Start Assessment
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Assessments</h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{sessions.length}</p>
              </div>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Assessment</h3>
                <p className="text-lg font-semibold text-gray-900 dark:text-white mt-2">
                  {new Date(sessions[0].created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Most Common Triage</h3>
                <p className="text-lg font-semibold text-gray-900 dark:text-white mt-2">
                  {triageLevelData.length > 0
                    ? triageLevelData.reduce((a, b) => b.value > a.value ? b : a).name
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Triage Level Distribution */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Triage Level Distribution
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={triageLevelData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {triageLevelData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Assessments Over Time */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Assessments Over Time
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={assessmentsOverTime}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Top Symptoms */}
              <div className="card lg:col-span-2">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Top Reported Symptoms
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={topSymptoms}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Session History Table */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Assessment History
              </h3>
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
                    {sessions.map((session) => (
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
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
