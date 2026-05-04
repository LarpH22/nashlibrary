import api from '../../shared/api.js'

export async function loginUser(credentials) {
  if (!credentials.email || !credentials.password) {
    throw new Error('Email and password are required')
  }
  try {
    const response = await api.post('/api/auth/login', {
      email: credentials.email,
      password: credentials.password,
      role: credentials.role // Optional role hint
    })
    return response.data
  } catch (error) {
    // Re-throw with proper error message
    if (error.response?.status === 401) {
      throw new Error('Invalid email or password')
    }
    throw error
  }
}

export async function registerUser(data) {
  if (!data.email || !data.password || !data.full_name || !data.registration_document) {
    throw new Error('Full name, email, password, and registration document are required')
  }

  const formData = new FormData()
  formData.append('email', data.email)
  formData.append('full_name', data.full_name)
  formData.append('password', data.password)
  formData.append('student_id', data.student_id || '')
  formData.append('department', data.department || '')
  formData.append('year_level', data.year_level || '')
  formData.append('role', 'student')
  formData.append('registration_document', data.registration_document)

  try {
    const response = await api.post('/api/auth/register', formData)
    return response.data
  } catch (error) {
    if (error.response?.status === 400) {
      throw new Error(error.response.data?.message || 'Registration failed')
    }
    throw error
  }
}

export async function forgotPassword(data) {
  if (!data.email) {
    throw new Error('Email is required')
  }
  try {
    const response = await api.post('/api/auth/forgot-password', {
      email: data.email
    })
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error('No active account found with this email')
    }
    throw error
  }
}

export async function resetPassword(data) {
  if (!data.token || !data.new_password) {
    throw new Error('Reset token and new password are required')
  }
  try {
    const response = await api.post('/api/auth/reset-password', {
      token: data.token,
      new_password: data.new_password
    })
    return response.data
  } catch (error) {
    if (error.response?.data?.message) {
      throw new Error(error.response.data.message)
    }
    throw new Error('Failed to reset password')
  }
}

export async function getUserProfile() {
  const response = await api.get('/api/auth/profile')
  return response.data
}
