import axios from 'axios'
import { clearStoredAuth, getStoredAuthToken, isJwtExpired } from './authStorage.js'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5000')
const LOGIN_PATH = '/login'

function isAuthRoute(url = '') {
  return ['/api/auth/login', '/api/auth/register', '/api/auth/forgot-password', '/api/auth/reset-password'].some((route) => url.includes(route))
}

function normalizeApiError(error, fallbackMessage = 'Request failed') {
  const status = error?.response?.status || 0
  const data = error?.response?.data
  const message = data?.message || data?.error || error?.message || fallbackMessage
  return { status, data, message }
}

function redirectToLoginForExpiredSession() {
  if (typeof window === 'undefined') {
    return
  }

  const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`
  if (window.location.pathname !== LOGIN_PATH) {
    window.history.replaceState({ sessionExpired: true }, '', LOGIN_PATH)
    window.dispatchEvent(new CustomEvent('auth:redirect-login', { detail: { from: currentPath } }))
  }
}

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false
})

// Request interceptor - add auth token and correct content type for FormData
api.interceptors.request.use(
  (config) => {
    config.headers = config.headers || {}
    const token = getStoredAuthToken()
    if (token) {
      if (isJwtExpired(token)) {
        clearStoredAuth()
        redirectToLoginForExpiredSession()
        const expiredError = new axios.AxiosError(
          'Session expired',
          'ERR_SESSION_EXPIRED',
          config,
          null,
          {
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            config,
            data: { message: 'Session expired', code: 'token_expired' }
          }
        )
        expiredError.response = {
          status: 401,
          data: { message: 'Session expired', code: 'token_expired' },
          config
        }
        return Promise.reject(expiredError)
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
    const authRequest = isAuthRoute(requestUrl)
    const normalized = normalizeApiError(error)

    if (normalized.status === 401 && !authRequest) {
      clearStoredAuth()
      redirectToLoginForExpiredSession()
      console.warn(`[API] Unauthorized response from protected endpoint: ${normalized.message}`)
    }

    console.error(`[API] Error ${normalized.status || 'network'}: ${normalized.message}`, normalized.data || '')
    return Promise.reject(error)
  }
)

export default api
export { normalizeApiError }
