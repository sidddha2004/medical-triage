import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { symptomAPI, sessionAPI } from '../lib/api'

interface Message {
  role: 'user' | 'agent' | 'system'
  content: string
  timestamp?: Date
}

interface TriageResult {
  session_id: number
  disease: string
  confidence: number
  triage_level: string
  precautions: string[]
  matched_symptoms: string[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [triageResult, setTriageResult] = useState<TriageResult | null>(null)
  const [showResults, setShowResults] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const token = useAuthStore((state) => state.token)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !token) {
      navigate('/login')
      return
    }

    // Connect to WebSocket with token
    const wsUrl = `ws://localhost:8000/ws/triage/?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'connected') {
        setMessages(prev => [...prev, {
          role: 'agent',
          content: data.message || 'Hello! I\'m your health triage assistant. Please describe your symptoms.',
          timestamp: new Date()
        }])
      } else if (data.type === 'message') {
        setMessages(prev => [...prev, {
          role: 'agent',
          content: data.content,
          timestamp: new Date()
        }])
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id)
        }
      } else if (data.type === 'error') {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Error: ${data.message}`,
          timestamp: new Date()
        }])
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!input.trim() || loading || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to chat
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }])

    // Send via WebSocket
    wsRef.current.send(JSON.stringify({
      message: userMessage,
      session_id: sessionId || undefined
    }))

    // Simulate agent response timeout (fallback)
    setTimeout(() => {
      setLoading(false)
    }, 5000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const extractSymptoms = async () => {
    // Extract symptoms from conversation
    const symptomKeywords = messages
      .filter(m => m.role === 'user')
      .map(m => m.content.toLowerCase())
      .join(' ')

    // Simple keyword extraction - in production, use NLP
    const commonSymptoms = [
      'fever', 'headache', 'cough', 'sore throat', 'fatigue',
      'nausea', 'vomiting', 'diarrhea', 'rash', 'pain',
      'dizziness', 'shortness of breath', 'chest pain', 'runny nose'
    ]

    const extractedSymptoms = commonSymptoms.filter(s => symptomKeywords.includes(s))

    if (extractedSymptoms.length === 0) {
      alert('No recognizable symptoms found. Please describe your symptoms more clearly.')
      return
    }

    setLoading(true)
    try {
      const response = await symptomAPI.submitAssessment(extractedSymptoms)
      if (response.data) {
        setTriageResult({
          session_id: response.data.session?.id || sessionId || 1,
          disease: response.data.prediction?.disease || 'Unknown',
          confidence: response.data.prediction?.confidence || 0,
          triage_level: response.data.triage_level || 'self_care',
          precautions: response.data.prediction?.precautions || [],
          matched_symptoms: response.data.prediction?.matched_symptoms || extractedSymptoms
        })
        setShowResults(true)
      }
    } catch (error: any) {
      console.error('Failed to submit assessment:', error)
      alert('Assessment failed: ' + (error.response?.data?.error || 'Unknown error'))
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

  const endSession = async () => {
    if (sessionId) {
      try {
        await sessionAPI.endSession(sessionId)
      } catch (error) {
        console.error('Failed to end session:', error)
      }
    }
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Symptom Assessment
              </h1>
            </div>
            <div className="flex items-center gap-4">
              {sessionId && (
                <span className="text-sm text-gray-500">
                  Session: #{sessionId}
                </span>
              )}
              <button onClick={endSession} className="btn-secondary">
                End Session
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 px-4">
        {/* Chat Area */}
        <div className="card h-[600px] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4 p-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                <p className="mb-2">Welcome to Health Triage Assistant</p>
                <p>Describe your symptoms and I'll help assess your condition.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : msg.role === 'system'
                        ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    <p className="text-sm">{msg.content}</p>
                    {msg.timestamp && (
                      <p className="text-xs opacity-70 mt-1">
                        {msg.timestamp.toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 dark:bg-gray-700 rounded-lg px-4 py-2">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t dark:border-gray-700 p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe your symptoms..."
                disabled={loading}
                className="input-field flex-1"
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="btn-primary disabled:opacity-50"
              >
                Send
              </button>
              <button
                onClick={extractSymptoms}
                disabled={messages.length === 0}
                className="btn-secondary disabled:opacity-50"
              >
                Get Assessment
              </button>
            </div>
          </div>
        </div>

        {/* Triage Results Modal */}
        {showResults && triageResult && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
                Triage Assessment Results
              </h2>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Detected Condition</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {triageResult.disease}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Confidence</p>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${triageResult.confidence * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                    {(triageResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Triage Level</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-white text-sm font-medium ${getTriageLevelColor(triageResult.triage_level)}`}>
                    {triageResult.triage_level.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                {triageResult.matched_symptoms.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Matched Symptoms</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {triageResult.matched_symptoms.map((symptom, idx) => (
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

                {triageResult.precautions.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Recommended Precautions</p>
                    <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 mt-1">
                      {triageResult.precautions.map((precaution, idx) => (
                        <li key={idx}>{precaution}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => setShowResults(false)}
                  className="btn-secondary flex-1"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    setShowResults(false)
                    navigate('/results')
                  }}
                  className="btn-primary flex-1"
                >
                  View Details
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
