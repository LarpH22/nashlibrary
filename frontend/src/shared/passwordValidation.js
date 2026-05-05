export const passwordRequirementText = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'

export function validatePassword(value, fieldLabel = 'Password') {
  if (!value) {
    return { isValid: false, message: `${fieldLabel} is required` }
  }
  if (value.length < 8) {
    return { isValid: false, message: `${fieldLabel} must be at least 8 characters long` }
  }
  if (!/[A-Z]/.test(value)) {
    return { isValid: false, message: `${fieldLabel} must contain at least one uppercase letter` }
  }
  if (!/[a-z]/.test(value)) {
    return { isValid: false, message: `${fieldLabel} must contain at least one lowercase letter` }
  }
  if (!/\d/.test(value)) {
    return { isValid: false, message: `${fieldLabel} must contain at least one number` }
  }
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
    return { isValid: false, message: `${fieldLabel} must contain at least one special character` }
  }
  return { isValid: true, message: 'Strong password!' }
}

export function validatePasswordConfirmation(password, confirmPassword) {
  if (!confirmPassword) {
    return { isValid: false, message: 'Confirm password is required' }
  }
  if (password !== confirmPassword) {
    return { isValid: false, message: 'Passwords do not match' }
  }
  return { isValid: true, message: 'Passwords match' }
}
