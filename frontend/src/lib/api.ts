import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add token to requests
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired - logout
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth APIs
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login/', { email, password }),
  register: (email: string, password: string, password_confirm: string) =>
    api.post('/auth/register/', { email, password, password_confirm }),
}

// Patient APIs
export const patientAPI = {
  getProfile: () => api.get('/patients/me/'),
  createProfile: (data: { date_of_birth?: string; gender?: string; blood_type?: string }) =>
    api.post('/patients/', data),
  updateProfile: (id: number, data: { date_of_birth?: string; gender?: string; blood_type?: string }) =>
    api.put(`/patients/${id}/`, data),
}

// Symptom Assessment APIs
export const symptomAPI = {
  submitAssessment: (symptoms: string[], notes?: string, patient_id?: number) =>
    api.post('/symptom-assessment/', { symptoms, notes, patient_id }),
}

// Session APIs
export const sessionAPI = {
  getSessions: (patient_id?: number) =>
    api.get('/sessions/', { params: { patient_id } }),
  getSession: (id: number) =>
    api.get(`/sessions/${id}/`),
  endSession: (id: number) =>
    api.post(`/sessions/${id}/end_session/`),
}

// Prediction APIs
export const predictionAPI = {
  getPredictions: (session_id?: number) =>
    api.get('/predictions/', { params: { session_id } }),
}

// ML APIs
export const mlAPI = {
  getStatus: () => api.get('/ml/status/'),
  getSymptoms: () => api.get('/ml/symptoms/'),
  getDiseases: () => api.get('/ml/diseases/'),
}

export default api
