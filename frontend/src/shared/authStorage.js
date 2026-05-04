const AUTH_STORAGE_KEYS = ['access_token', 'token', 'user_role', 'user_id', 'user_email']
export const AUTH_SESSION_CLEARED_EVENT = 'auth:session-cleared'

export function getStoredAuthToken() {
  return localStorage.getItem('access_token') || localStorage.getItem('token') || ''
}

export function clearStoredAuth() {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key))
  window.dispatchEvent(new Event(AUTH_SESSION_CLEARED_EVENT))
}

export function saveLoginSession(data) {
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user_role', data.role)
  localStorage.setItem('user_email', data.email)
  const payload = decodeJwtPayload(data.access_token) || {}
  const userId = data.user_id || data.student_id || data.librarian_id || data.admin_id || payload.student_id || payload.librarian_id || payload.admin_id || ''
  if (userId) {
    localStorage.setItem('user_id', String(userId))
  }
}

export function decodeJwtPayload(token) {
  if (!token || token.split('.').length !== 3) {
    return null
  }

  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), '=')
    const decoded = atob(padded)
    const json = decodeURIComponent(
      decoded
        .split('')
        .map((char) => `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`)
        .join('')
    )
    return JSON.parse(json)
  } catch (error) {
    console.warn('[authStorage] Unable to decode JWT payload', error)
    return null
  }
}

export function isJwtExpired(token, clockSkewSeconds = 30) {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) {
    return false
  }

  return Math.floor(Date.now() / 1000) >= Number(payload.exp) - clockSkewSeconds
}

export function getStoredUserRole() {
  const token = getStoredAuthToken()
  const tokenRole = decodeJwtPayload(token)?.role
  return tokenRole || localStorage.getItem('user_role') || ''
}
