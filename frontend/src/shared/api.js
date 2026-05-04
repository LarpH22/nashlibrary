import axios from 'axios'
import { clearStoredAuth, getStoredAuthToken, isJwtExpired } from './authStorage.js'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5000')

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false
})

// Request interceptor - add auth token and correct content type for FormData
api.interceptors.request.use(
  (config) => {
    const token = getStoredAuthToken()
    if (token) {
      if (isJwtExpired(token)) {
        clearStoredAuth()
        return Promise.reject(new axios.Cancel('Session expired'))
      }

      config.headers.Authorization = `Bearer ${token}`
    }

    // Allow the browser/axios to set the correct multipart boundary for FormData
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    } else {
      config.headers['Content-Type'] = 'application/json'
    }

    console.debug(`[API] ${config.method.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => {
    console.debug(`[API] Response ${response.status}: ${response.config.method.toUpperCase()} ${response.config.url}`)
    return response
  },
  (error) => {
    const requestUrl = error.config?.url || ''
    const isAuthRequest = requestUrl.includes('/api/auth/login') || requestUrl.includes('/api/auth/register')

    if (error.response?.status === 401 && !isAuthRequest) {
      console.warn('[API] Unauthorized response from protected endpoint')
    }
    console.error(`[API] Error ${error.response?.status}:`, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
