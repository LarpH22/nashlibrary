import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerUser } from './authService.js'

export function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    student_id: '',
    department: '',
    year_level: '',
    registration_document: null
  })
  const [validation, setValidation] = useState({
    full_name: { isValid: null, message: 'Full name is required' },
    email: { isValid: null, message: 'Email is required (only Gmail or .edu.ph domains allowed)' },
    password: { isValid: null, message: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character' },
    student_id: { isValid: null, message: 'Student ID must follow format: 241-0449 (3 digits + dash + 4 digits)' },
    department: { isValid: null, message: 'Department / Program is required' },
    year_level: { isValid: null, message: 'Year level is required' },
    registration_document: { isValid: null, message: 'Please upload a PDF, JPG, JPEG, or PNG file (max 5MB)' }
  })
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Validation functions
  const validateFullName = (value) => {
    if (!value.trim()) {
      return { isValid: false, message: 'Full name is required' }
    }
    if (value.trim().length < 2) {
      return { isValid: false, message: 'Full name must be at least 2 characters' }
    }
    if (value.trim().length > 100) {
      return { isValid: false, message: 'Full name must be less than 100 characters' }
    }
    return { isValid: true, message: 'Looks good!' }
  }

  const validateEmail = (value) => {
    if (!value.trim()) {
      return { isValid: false, message: 'Email is required' }
    }

    // More strict email regex pattern
    const emailPattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

    if (!emailPattern.test(value)) {
      return { isValid: false, message: 'Please enter a valid email address format' }
    }

    // Extract domain from email
    const emailParts = value.split('@')
    if (emailParts.length !== 2) {
      return { isValid: false, message: 'Invalid email format' }
    }

    const domain = emailParts[1].toLowerCase()

    // Check allowed domains
    const allowedDomains = ['gmail.com']
    const isEduPhDomain = domain.endsWith('.edu.ph')

    if (!allowedDomains.includes(domain) && !isEduPhDomain) {
      return { isValid: false, message: 'Only Gmail (gmail.com) and educational domains (.edu.ph) are allowed' }
    }

    // Additional validation for educational domains
    if (isEduPhDomain && domain.length <= 7) { // ".edu.ph" is 7 chars, so domain must be longer
      return { isValid: false, message: 'Invalid educational domain format' }
    }

    // Basic checks for email deliverability
    const localPart = emailParts[0]
    if (localPart.length === 0 || localPart.length > 64) {
      return { isValid: false, message: 'Invalid email local part length' }
    }

    if (domain.length === 0 || domain.length > 253) {
      return { isValid: false, message: 'Invalid email domain length' }
    }

    // Check for consecutive dots
    if (localPart.includes('..') || domain.includes('..')) {
      return { isValid: false, message: 'Email cannot contain consecutive dots' }
    }

    // Check for starting/ending with dots
    if (localPart.startsWith('.') || localPart.endsWith('.') ||
        domain.startsWith('.') || domain.endsWith('.')) {
      return { isValid: false, message: 'Email cannot start or end with dots' }
    }

    return { isValid: true, message: 'Valid email address for verification' }
  }

  const validatePassword = (value) => {
    if (!value) {
      return { isValid: false, message: 'Password is required' }
    }
    if (value.length < 8) {
      return { isValid: false, message: 'Password must be at least 8 characters long' }
    }
    if (!/[A-Z]/.test(value)) {
      return { isValid: false, message: 'Password must contain at least one uppercase letter' }
    }
    if (!/[a-z]/.test(value)) {
      return { isValid: false, message: 'Password must contain at least one lowercase letter' }
    }
    if (!/\d/.test(value)) {
      return { isValid: false, message: 'Password must contain at least one number' }
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
      return { isValid: false, message: 'Password must contain at least one special character' }
    }
    return { isValid: true, message: 'Strong password!' }
  }

  const validateStudentId = (value) => {
    if (!value.trim()) {
      return { isValid: false, message: 'Student ID is required' }
    }
    const pattern = /^\d{3}-\d{4}$/
    if (!pattern.test(value.trim())) {
      return { isValid: false, message: 'Student ID must follow format: 241-0449 (3 digits + dash + 4 digits)' }
    }
    return { isValid: true, message: 'Valid student ID format' }
  }

  const validateDepartment = (value) => {
    if (!value.trim()) {
      return { isValid: false, message: 'Department / Program is required' }
    }
    if (value.trim().length > 100) {
      return { isValid: false, message: 'Department / Program must be less than 100 characters' }
    }
    return { isValid: true, message: 'Valid department / program' }
  }

  const validateYearLevel = (value) => {
    if (!String(value).trim()) {
      return { isValid: false, message: 'Year level is required' }
    }
    const numeric = Number(value)
    if (!Number.isInteger(numeric) || numeric < 1 || numeric > 10) {
      return { isValid: false, message: 'Year level must be a number from 1 to 10' }
    }
    return { isValid: true, message: 'Valid year level' }
  }

  const validateFile = (file) => {
    if (!file) {
      return { isValid: false, message: 'Registration document is required' }
    }

    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    if (!allowedTypes.includes(file.type)) {
      return { isValid: false, message: 'File must be PDF, JPG, JPEG, or PNG' }
    }

    const maxSize = 5 * 1024 * 1024 // 5MB
    if (file.size > maxSize) {
      return { isValid: false, message: 'File size must be less than 5MB' }
    }

    return { isValid: true, message: 'File looks good!' }
  }

  const handleChange = (event) => {
    const { name, value, files } = event.target

    if (name === 'registration_document') {
      const file = files?.[0] || null
      setForm({
        ...form,
        registration_document: file
      })
      setValidation({
        ...validation,
        registration_document: validateFile(file)
      })
      return
    }

    setForm({
      ...form,
      [name]: value
    })

    // Validate the field
    let validationResult
    switch (name) {
      case 'full_name':
        validationResult = validateFullName(value)
        break
      case 'email':
        validationResult = validateEmail(value)
        break
      case 'password':
        validationResult = validatePassword(value)
        break
      case 'student_id':
        validationResult = validateStudentId(value)
        break
      case 'department':
        validationResult = validateDepartment(value)
        break
      case 'year_level':
        validationResult = validateYearLevel(value)
        break
      default:
        validationResult = { isValid: null, message: '' }
    }

    setValidation({
      ...validation,
      [name]: validationResult
    })
  }

  // Validate all fields on form submission
  const validateForm = () => {
    const validations = {
      full_name: validateFullName(form.full_name),
      email: validateEmail(form.email),
      password: validatePassword(form.password),
      student_id: validateStudentId(form.student_id),
      department: validateDepartment(form.department),
      year_level: validateYearLevel(form.year_level),
      registration_document: validateFile(form.registration_document)
    }

    setValidation(validations)

    // Check if all validations pass
    return Object.values(validations).every(v => v.isValid === true)
  }

  const getInputClass = (fieldName) => {
    const fieldValidation = validation[fieldName]
    if (fieldValidation.isValid === true) return 'input-valid'
    if (fieldValidation.isValid === false) return 'input-invalid'
    return ''
  }

  const getMessageClass = (fieldName) => {
    const fieldValidation = validation[fieldName]
    if (fieldValidation.isValid === true) return 'validation-message success'
    if (fieldValidation.isValid === false) return 'validation-message error'
    return 'validation-message neutral'
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!validateForm()) {
      setMessage('Please fix the validation errors before submitting.')
      return
    }

    setIsLoading(true)
    try {
      const data = await registerUser(form)
      // Registration successful - show verification message
      setMessage(`Registration request submitted successfully! Please check your email at ${form.email} to verify your account. Your account will be pending admin approval after verification.`)
      console.log('Registration successful:', data)
      // Clear form
      setForm({
        full_name: '',
        email: '',
        password: '',
        student_id: '',
        department: '',
        year_level: '',
        registration_document: null
      })
      // Reset validation
      setValidation({
        full_name: { isValid: null, message: 'Full name is required' },
        email: { isValid: null, message: 'Email is required (only Gmail or .edu.ph domains allowed)' },
        password: { isValid: null, message: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character' },
        student_id: { isValid: null, message: 'Student ID must follow format: 241-0449 (3 digits + dash + 4 digits)' },
        department: { isValid: null, message: 'Department / Program is required' },
        year_level: { isValid: null, message: 'Year level is required' },
        registration_document: { isValid: null, message: 'Please upload a PDF, JPG, JPEG, or PNG file (max 5MB)' }
      })
      // Don't navigate or set tokens - user needs to verify email first
    } catch (error) {
      const errorMsg = error.message || 'Registration failed'
      console.error('Registration error:', errorMsg, error)
      setMessage(`Error: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <h2>Register</h2>
        <p className="auth-card-subtitle">Create your account to start borrowing books and managing your library profile.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Full Name
            <input
              type="text"
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              className={getInputClass('full_name')}
              required
            />
            <span className={getMessageClass('full_name')}>
              {validation.full_name.message}
            </span>
          </label>
          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              className={getInputClass('email')}
              required
            />
            <span className={getMessageClass('email')}>
              {validation.email.message}
            </span>
          </label>
          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              className={getInputClass('password')}
              required
            />
            <span className={getMessageClass('password')}>
              {validation.password.message}
            </span>
          </label>
          <label>
            Student ID
            <input
              type="text"
              name="student_id"
              value={form.student_id}
              onChange={handleChange}
              className={getInputClass('student_id')}
              placeholder="e.g., 241-0449"
              required
            />
            <span className={getMessageClass('student_id')}>
              {validation.student_id.message}
            </span>
          </label>
          <label>
            Department / Program
            <input
              type="text"
              name="department"
              value={form.department}
              onChange={handleChange}
              className={getInputClass('department')}
              placeholder="e.g., Computer Science"
              required
            />
            <span className={getMessageClass('department')}>
              {validation.department.message}
            </span>
          </label>
          <label>
            Year Level
            <input
              type="number"
              name="year_level"
              value={form.year_level}
              onChange={handleChange}
              className={getInputClass('year_level')}
              min="1"
              max="10"
              placeholder="e.g., 1"
              required
            />
            <span className={getMessageClass('year_level')}>
              {validation.year_level.message}
            </span>
          </label>
          <label>
            Registration Document
            <input
              type="file"
              name="registration_document"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleChange}
              className={getInputClass('registration_document')}
              required
            />
            {form.registration_document && (
              <span className="file-name">Selected: {form.registration_document.name}</span>
            )}
            <span className={getMessageClass('registration_document')}>
              {validation.registration_document.message}
            </span>
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Registering...' : 'Submit'}
          </button>
        </form>
      <div className="auth-card-footer">
        <span>Already have an account?</span>
        <button type="button" className="auth-link" onClick={() => navigate('/login')}>Sign in</button>
      </div>
      {message && (
        <div className={`message ${message.includes('Error') || message.includes('fix') ? 'error' : 'success'}`}>
          <p>{message}</p>
        </div>
      )}
    </section>
  </div>
  )
}
