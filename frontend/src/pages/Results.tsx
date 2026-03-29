import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { sessionAPI, predictionAPI } from '../lib/api'

interface Session {
  id: number
  status: string
  triage_level: string
  created_at: string
  primary_symptoms: string[]
}

interface Prediction {
  id: number
  disease: string
  confidence: number
  symptoms_analyzed: string[]
}

export default function Results() {
  const [session, setSession] = useState<Session | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [searchParams] = useSearchParams()

  const sessionId = searchParams.get('session')

  useEffect(() => {
    if (sessionId) {
      loadSessionData(parseInt(sessionId))
    } else {
      // Load latest session if no session param
      loadLatestSession()
    }
  }, [sessionId])

  const loadLatestSession = async () => {
    try {
      const sessionsRes = await sessionAPI.getSessions()
      const sessions = sessionsRes.data.results || sessionsRes.data || []
      if (sessions.length > 0) {
        loadSessionData(sessions[0].id)
      } else {
        setLoading(false)
      }
    } catch (error) {
      console.error('Failed to load latest session:', error)
      setLoading(false)
    }
  }

  const loadSessionData = async (id: number) => {
    try {
      const [sessionRes, predictionsRes] = await Promise.all([
        sessionAPI.getSession(id),
        predictionAPI.getPredictions(id)
      ])
      setSession(sessionRes.data)
      setPredictions(predictionsRes.data.results || predictionsRes.data || [])
    } catch (error) {
      console.error('Failed to load session data:', error)
      setSession(null)
      setPredictions([])
    } finally {
      setLoading(false)
    }
  }

  const getTriageLevelColor = (level: string) => {
    switch (level) {
      case 'emergency': return 'bg-red-600'
      case 'urgent_care': return 'bg-orange-500'
      case 'gp_visit': return 'bg-yellow-500'
      case 'self_care': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Assessment Results
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

      <main className="max-w-4xl mx-auto py-6 px-4">
        {loading ? (
          <div className="card text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 dark:text-gray-400 mt-2">Loading results...</p>
          </div>
        ) : !session && !sessionId ? (
          <div className="card text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No assessment selected. View your latest results or start a new assessment.
            </p>
            <Link to="/chat" className="btn-primary">
              Start New Assessment
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Session Overview */}
            {session && (
              <div className="card">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                      Assessment #{session.id}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(session.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-white text-sm font-medium ${getTriageLevelColor(session.triage_level || 'self_care')}`}>
                    {(session.triage_level || 'N/A').replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                {session.primary_symptoms && session.primary_symptoms.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Symptoms Reported
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {session.primary_symptoms.map((symptom, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm text-gray-700 dark:text-gray-300"
                        >
                          {symptom}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-4 pt-4 border-t dark:border-gray-700">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Status: <span className="font-medium">{session.status}</span>
                    </span>
                    <Link to={`/chat`} className="text-primary-600 hover:text-primary-500 text-sm">
                      Continue Assessment →
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* Predictions */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                AI Analysis
              </h3>
              {predictions.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                  No predictions available for this assessment.
                </p>
              ) : (
                <div className="space-y-4">
                  {predictions.map((prediction) => (
                    <div
                      key={prediction.id}
                      className="border dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {prediction.disease}
                        </h4>
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                          {(prediction.confidence * 100).toFixed(1)}% confidence
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-3">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${prediction.confidence * 100}%` }}
                        ></div>
                      </div>
                      {prediction.symptoms_analyzed && prediction.symptoms_analyzed.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                            Matched Symptoms:
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {prediction.symptoms_analyzed.map((symptom, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs"
                              >
                                {symptom}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recommended Actions */}
            <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
                Recommended Actions
              </h3>
              <ul className="space-y-2 text-blue-800 dark:text-blue-200">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Monitor your symptoms and note any changes</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Stay hydrated and get plenty of rest</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Follow the triage level recommendation above</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Seek immediate medical attention if symptoms worsen</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
