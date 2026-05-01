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
  formData.append('role', 'student')
  formData.append('registration_document', data.registration_document)

  if (data.student_id) {
    formData.append('student_id', data.student_id)
  }

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

export async function getUserProfile() {
  try {
    const response = await api.get('/api/auth/profile')
    return response.data
  } catch (error) {
    throw error
  }
}
