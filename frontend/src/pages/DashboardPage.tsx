import { useState, type FormEvent } from 'react'
import { api, ApiError, type AssistanceResult } from '../api/client'
import { useAuth } from '../context/AuthContext'
import './DashboardPage.css'

export function DashboardPage() {
  const { token, user } = useAuth()
  const [requirements, setRequirements] = useState('')
  const [userStories, setUserStories] = useState('')
  const [codeDiffs, setCodeDiffs] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AssistanceResult | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await api.assist(token, {
        requirements,
        user_stories: userStories || null,
        code_diffs: codeDiffs || null,
        session_id: sessionId,
      })
      setResult(data)
      setSessionId(data.session_id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = () => {
    setSessionId(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="dashboard">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Hello, {user?.full_name?.split(' ')[0] ?? 'there'}</h1>
          <p className="hero-text">
            Submit requirements and let the Quality Assistant agents plan tests, data, and release
            guidance across your STLC.
          </p>
        </div>
        {sessionId && (
          <button type="button" className="btn btn-ghost" onClick={startNewSession}>
            New session
          </button>
        )}
      </section>

      <div className="dashboard-grid">
        <form className="panel input-panel" onSubmit={handleSubmit}>
          <h2>Input</h2>
          <label>
            Software requirements
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={6}
              placeholder="Describe features, acceptance criteria, and constraints..."
              required
            />
          </label>
          <label>
            User stories (optional)
            <textarea
              value={userStories}
              onChange={(e) => setUserStories(e.target.value)}
              rows={4}
              placeholder="As a user, I want..."
            />
          </label>
          <label>
            Code diffs (optional)
            <textarea
              value={codeDiffs}
              onChange={(e) => setCodeDiffs(e.target.value)}
              rows={4}
              placeholder="Paste git diff for change-impact aware suggestions..."
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading || !requirements.trim()}
          >
            {loading ? 'Running quality assistance...' : 'Get quality assistance'}
          </button>
        </form>

        <section className="panel output-panel">
          <h2>Results</h2>
          {error && <div className="banner banner-error">{error}</div>}
          {!error && !result && !loading && (
            <p className="muted">Submit requirements to generate structured QA guidance.</p>
          )}
          {loading && <p className="muted pulse">Contacting agent service...</p>}
          {result && (
            <article className="result">
              <div className="result-meta">
                <span className={`badge badge-${result.status}`}>{result.status}</span>
                <span>Session: {result.session_id}</span>
              </div>
              <pre className="response">{result.response}</pre>
            </article>
          )}
        </section>
      </div>
    </div>
  )
}
