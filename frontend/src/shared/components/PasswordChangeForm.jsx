import { useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, Eye, EyeOff } from 'lucide-react'
import { passwordRequirementText, validatePassword, validatePasswordConfirmation } from '../passwordValidation.js'

const fieldLabels = {
  old_password: 'Current password',
  new_password: 'New password',
  confirm_password: 'Confirm password'
}

const emptyVisibility = {
  old_password: false,
  new_password: false,
  confirm_password: false
}

export function getPasswordChangeValidation(form) {
  if (!form.old_password || !form.new_password) {
    return { isValid: false, message: 'Current password and new password are required.' }
  }

  const passwordValidation = validatePassword(form.new_password, 'New password')
  if (!passwordValidation.isValid) {
    return passwordValidation
  }

  const confirmationValidation = validatePasswordConfirmation(form.new_password, form.confirm_password)
  if (!confirmationValidation.isValid) {
    return confirmationValidation
  }

  if (form.old_password === form.new_password) {
    return { isValid: false, message: 'New password must be different from current password' }
  }

  return { isValid: true, message: 'Password is ready to save' }
}

export function PasswordChangeForm({
  form,
  onFieldChange,
  onSubmit,
  error = '',
  success = '',
  submitting = false,
  submitLabel = 'Save password'
}) {
  const [visibleFields, setVisibleFields] = useState(emptyVisibility)
  const [touched, setTouched] = useState({})

  const validation = useMemo(() => {
    const newPassword = form.new_password
    const confirmPassword = form.confirm_password
    return {
      old_password: form.old_password
        ? { isValid: true, message: 'Current password entered' }
        : { isValid: false, message: 'Current password is required' },
      new_password: newPassword
        ? validatePassword(newPassword, 'New password')
        : { isValid: false, message: passwordRequirementText },
      confirm_password: confirmPassword
        ? validatePasswordConfirmation(newPassword, confirmPassword)
        : { isValid: false, message: 'Confirm password is required' }
    }
  }, [form])

  const changeField = (field, value) => {
    onFieldChange(field, value)
    setTouched((current) => ({ ...current, [field]: true }))
  }

  const toggleField = (field) => {
    setVisibleFields((current) => ({ ...current, [field]: !current[field] }))
  }

  const renderField = (field, placeholder, autoComplete) => {
    const state = validation[field]
    const showState = touched[field] || Boolean(form[field])
    const isVisible = visibleFields[field]
    return (
      <div className="fgroup password-field-group">
        <label htmlFor={`password-${field}`}>{fieldLabels[field]}</label>
        <div className="password-input-wrap">
          <input
            id={`password-${field}`}
            type={isVisible ? 'text' : 'password'}
            value={form[field]}
            onChange={(event) => changeField(field, event.target.value)}
            onBlur={() => setTouched((current) => ({ ...current, [field]: true }))}
            placeholder={placeholder}
            autoComplete={autoComplete}
            aria-invalid={showState && !state.isValid ? 'true' : undefined}
            aria-describedby={`password-${field}-message`}
          />
          <button
            className="password-toggle"
            type="button"
            onClick={() => toggleField(field)}
            aria-label={isVisible ? `Hide ${fieldLabels[field]}` : `Show ${fieldLabels[field]}`}
          >
            {isVisible ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
          </button>
        </div>
        <div
          id={`password-${field}-message`}
          className={`password-field-message ${showState && state.isValid ? 'valid' : showState ? 'invalid' : ''}`}
        >
          {showState && state.isValid ? <CheckCircle2 size={13} aria-hidden="true" /> : <AlertCircle size={13} aria-hidden="true" />}
          <span>{state.message}</span>
        </div>
      </div>
    )
  }

  return (
    <form className="password-change-form" onSubmit={onSubmit} noValidate>
      <div className="password-change-grid">
        {renderField('old_password', 'Current password', 'current-password')}
        {renderField('new_password', passwordRequirementText, 'new-password')}
        {renderField('confirm_password', 'Confirm new password', 'new-password')}
      </div>
      {error && <div className="password-feedback error-message">{error}</div>}
      {success && <div className="password-feedback success-message">{success}</div>}
      <div className="password-actions">
        <button className="btn btn-gold" type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : submitLabel}
        </button>
      </div>
    </form>
  )
}
