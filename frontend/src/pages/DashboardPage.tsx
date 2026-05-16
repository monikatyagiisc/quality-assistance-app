import { useState, type FormEvent } from 'react'
import { api, type AssistanceResult } from '../api/client'
import { getUserFriendlyError } from '../utils/errorMessages'
import { ASSISTANCE_SAMPLES } from '../data/assistanceSamples'
import { useAuth } from '../context/AuthContext'
import './DashboardPage.css'

export function DashboardPage() {
  const { token, user } = useAuth()
  const [requirements, setRequirements] = useState('')
  const [userStories, setUserStories] = useState('')
  const [codeDiffs, setCodeDiffs] = useState('')
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AssistanceResult | null>(null)

  const selectedSample = ASSISTANCE_SAMPLES.find((s) => s.id === selectedSampleId)

  const loadSample = (sampleId: string) => {
    const sample = ASSISTANCE_SAMPLES.find((s) => s.id === sampleId)
    if (!sample) return

    if (sample.requiresSession && !sessionId) {
      setError('Run another sample first, then load the follow-up sample in the same session.')
      return
    }

    setSelectedSampleId(sample.id)
    setRequirements(sample.requirements)
    setUserStories(sample.userStories)
    setCodeDiffs(sample.codeDiffs)
    setError(null)
    if (!sample.requiresSession) {
      setResult(null)
    }
  }

  const clearForm = () => {
    setSelectedSampleId(null)
    setRequirements('')
    setUserStories('')
    setCodeDiffs('')
    setError(null)
    setResult(null)
  }

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
      setError(getUserFriendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = () => {
    setSessionId(null)
    setResult(null)
    setError(null)
    setSelectedSampleId(null)
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
          <div className="input-panel-header">
            <h2>Input</h2>
            {(requirements || userStories || codeDiffs) && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={clearForm}>
                Clear
              </button>
            )}
          </div>

          <section className="samples-section" aria-label="Sample inputs">
            <p className="samples-intro">
              Try a sample to pre-fill the form. Edit fields before submitting if you like.
            </p>
            <div className="sample-grid">
              {ASSISTANCE_SAMPLES.map((sample) => (
                <button
                  key={sample.id}
                  type="button"
                  className={`sample-card${selectedSampleId === sample.id ? ' sample-card-active' : ''}${
                    sample.requiresSession && !sessionId ? ' sample-card-disabled' : ''
                  }`}
                  onClick={() => loadSample(sample.id)}
                  disabled={loading}
                  title={
                    sample.requiresSession && !sessionId
                      ? 'Complete a run first to enable follow-up'
                      : sample.description
                  }
                >
                  <span className="sample-card-title">{sample.title}</span>
                  <span className="sample-card-desc">{sample.description}</span>
                  <span className="sample-card-focus">{sample.focus}</span>
                </button>
              ))}
            </div>
            {selectedSample && (
              <p className="sample-loaded muted">
                Loaded: <strong>{selectedSample.title}</strong>
                {selectedSample.requiresSession && sessionId && ' · using current session'}
              </p>
            )}
          </section>

          <label>
            Software requirements
            <textarea
              value={requirements}
              onChange={(e) => {
                setRequirements(e.target.value)
                setSelectedSampleId(null)
              }}
              rows={6}
              placeholder="Describe features, acceptance criteria, and constraints..."
              required
            />
          </label>
          <label>
            User stories (optional)
            <textarea
              value={userStories}
              onChange={(e) => {
                setUserStories(e.target.value)
                setSelectedSampleId(null)
              }}
              rows={4}
              placeholder="As a user, I want..."
            />
          </label>
          <label>
            Code diffs (optional)
            <textarea
              value={codeDiffs}
              onChange={(e) => {
                setCodeDiffs(e.target.value)
                setSelectedSampleId(null)
              }}
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
            <p className="muted">Submit requirements or load a sample to generate QA guidance.</p>
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
