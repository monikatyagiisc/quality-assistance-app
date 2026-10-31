import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/useAuth'
import '../components/AuthForm.css'

export function LoginPage() {
  const { login, completeEntraSignIn, user, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(() =>
    (() => {
      const result = new URLSearchParams(window.location.search).get('sso')
      if (result === 'link-required') {
        return 'This email already has an app account. Sign in with email and password, then link Microsoft in Settings.'
      }
      if (result === 'error') {
        return 'Microsoft sign-in could not be completed. Please try again or use your email and password.'
      }
      return null
    })(),
  )
  const [submitting, setSubmitting] = useState(() =>
    new URLSearchParams(window.location.hash.slice(1)).has('sso_ticket'),
  )
  const [entraEnabled, setEntraEnabled] = useState(false)

  useEffect(() => {
    let active = true
    void api.getEntraSsoStatus()
      .then(({ enabled }) => {
        if (active) setEntraEnabled(enabled)
      })
      .catch((err) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Could not load sign-in options')
      })

    const ticket = new URLSearchParams(window.location.hash.slice(1)).get('sso_ticket')
    if (ticket) {
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`)
      void completeEntraSignIn(ticket)
        .then(() => navigate('/dashboard', { replace: true }))
        .catch((err) => {
          setError(err instanceof ApiError ? err.message : 'Microsoft sign-in failed')
        })
        .finally(() => setSubmitting(false))
    } else if (new URLSearchParams(window.location.search).has('sso')) {
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.hash}`)
    }

    return () => {
      active = false
    }
  }, [completeEntraSignIn, navigate])

  if (!loading && user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Sign in failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Welcome back</h1>
        <p className="auth-subtitle">Sign in to run quality assistance workflows.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </label>

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {entraEnabled && (
          <>
            <div className="auth-divider"><span>or</span></div>
            <button
              type="button"
              className="btn btn-ghost btn-block"
              disabled={submitting}
              onClick={async () => {
                setError(null)
                setSubmitting(true)
                try {
                  const { authorization_url } = await api.startEntraSignIn()
                  window.location.assign(authorization_url)
                } catch (err) {
                  setError(err instanceof ApiError ? err.message : 'Could not start Microsoft sign-in')
                  setSubmitting(false)
                }
              }}
            >
              Sign in with Microsoft
            </button>
          </>
        )}

        <p className="auth-footer">
          No account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  )
}
