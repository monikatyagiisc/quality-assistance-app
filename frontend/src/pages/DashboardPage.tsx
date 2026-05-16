import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, type AssistanceResult, type RepositoryConnection } from '../api/client'
import { getUserFriendlyError } from '../utils/errorMessages'
import { ASSISTANCE_SAMPLES } from '../data/assistanceSamples'
import { useAuth } from '../context/AuthContext'
import { SettingsInfoLink } from '../components/SettingsInfoLink'
import './DashboardPage.css'

const DIFF_SETTINGS_REQUIRED_MSG =
  'Code diffs require a saved GitHub repository and PAT. Add them in Settings before pasting.'

function isGithubFetchReady(
  connection: RepositoryConnection | null,
): connection is RepositoryConnection {
  return Boolean(connection?.owner && connection?.repo && connection.has_token)
}

function canAcceptCodeDiffs(connection: RepositoryConnection | null, value: string): boolean {
  return !value.trim() || isGithubFetchReady(connection)
}

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
  const [repoConnection, setRepoConnection] = useState<RepositoryConnection | null>(null)
  const [diffMode, setDiffMode] = useState<'paste' | 'fetch'>('paste')
  const [pullNumber, setPullNumber] = useState('')
  const [compareHead, setCompareHead] = useState('')
  const [diffImporting, setDiffImporting] = useState(false)
  const [diffImportNote, setDiffImportNote] = useState<string | null>(null)

  const selectedSample = ASSISTANCE_SAMPLES.find((s) => s.id === selectedSampleId)

  useEffect(() => {
    if (!token) return
    void api.getRepositorySettings(token).then(setRepoConnection).catch(() => setRepoConnection(null))
  }, [token])

  const applyCodeDiffs = (nextValue: string): boolean => {
    if (!canAcceptCodeDiffs(repoConnection, nextValue)) {
      setError(DIFF_SETTINGS_REQUIRED_MSG)
      return false
    }
    setCodeDiffs(nextValue)
    setSelectedSampleId(null)
    setDiffImportNote(null)
    return true
  }

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
    if (sample.codeDiffs.trim() && !isGithubFetchReady(repoConnection)) {
      setCodeDiffs('')
      setError(DIFF_SETTINGS_REQUIRED_MSG)
    } else {
      setCodeDiffs(sample.codeDiffs)
      setError(null)
    }
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

    if (codeDiffs.trim() && !isGithubFetchReady(repoConnection)) {
      setError(DIFF_SETTINGS_REQUIRED_MSG)
      return
    }

    if (diffMode === 'fetch') {
      if (!isGithubFetchReady(repoConnection)) {
        setError(
          'From GitHub requires a repository and personal access token. Configure both in Settings.',
        )
        return
      }
      if (!codeDiffs.trim()) {
        setError('Import a diff from GitHub before submitting, or switch to Paste.')
        return
      }
    }

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

  const importDiffFromRepo = async () => {
    if (!token) return

    const connection = repoConnection
    if (!isGithubFetchReady(connection)) {
      setError(
        'From GitHub requires a saved repository and PAT. Open Settings to add both.',
      )
      return
    }

    setDiffImporting(true)
    setError(null)
    setDiffImportNote(null)

    try {
      const pull = pullNumber.trim() ? Number(pullNumber) : null
      const head = compareHead.trim() || null

      if (pull !== null && (!Number.isInteger(pull) || pull < 1)) {
        setError('Enter a valid pull request number.')
        return
      }
      if (!pull && !head) {
        setError('Enter a PR number or a head branch/SHA to compare.')
        return
      }

      const fetched = await api.fetchRepositoryDiff(token, {
        pull_number: pull,
        head,
        base: connection.default_branch,
      })
      setCodeDiffs(fetched.diff)
      setSelectedSampleId(null)
      setDiffMode('paste')
      setDiffImportNote(`Imported ${fetched.summary}`)
    } catch (err) {
      setError(getUserFriendlyError(err))
    } finally {
      setDiffImporting(false)
    }
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
          <div className="diff-section">
            <div className="diff-section-header">
              <div className="diff-section-label">
                <span>Code diffs (optional)</span>
                <SettingsInfoLink label="Set up GitHub repository and PAT in Settings for automatic diff import" />
              </div>
              <div className="diff-mode-toggle" role="tablist" aria-label="Diff input mode">
                <button
                  type="button"
                  role="tab"
                  aria-selected={diffMode === 'paste'}
                  className={diffMode === 'paste' ? 'active' : ''}
                  onClick={() => setDiffMode('paste')}
                >
                  Paste
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={diffMode === 'fetch'}
                  className={diffMode === 'fetch' ? 'active' : ''}
                  onClick={() => setDiffMode('fetch')}
                >
                  From GitHub
                </button>
              </div>
            </div>

            {diffMode === 'paste' && (
              <>
                <label className="diff-paste-label">
                  <span className="sr-only">Code diffs</span>
                  <textarea
                    value={codeDiffs}
                    onChange={(e) => {
                      applyCodeDiffs(e.target.value)
                    }}
                    onPaste={(e) => {
                      const pasted = e.clipboardData.getData('text')
                      if (!pasted.trim() || isGithubFetchReady(repoConnection)) return
                      e.preventDefault()
                      setError(DIFF_SETTINGS_REQUIRED_MSG)
                    }}
                    rows={4}
                    placeholder="Paste git diff output (e.g. from git diff or a PR) for change-impact analysis..."
                  />
                </label>
                {!isGithubFetchReady(repoConnection) && (
                  <p className="diff-paste-hint muted">
                    Save repository and PAT in <Link to="/settings">Settings</Link> before pasting a
                    diff.
                  </p>
                )}
              </>
            )}

            {diffMode === 'fetch' && isGithubFetchReady(repoConnection) && (
              <div className="diff-fetch-panel">
                <p className="muted diff-fetch-repo">
                  Repository: <strong>{repoConnection!.repo_label}</strong> · base{' '}
                  <strong>{repoConnection!.default_branch}</strong>
                </p>
                <label>
                  Pull request #
                  <input
                    type="number"
                    min={1}
                    value={pullNumber}
                    onChange={(e) => setPullNumber(e.target.value)}
                    placeholder="42"
                  />
                </label>
                <p className="diff-fetch-or muted">or compare head branch / SHA</p>
                <label>
                  Head ref
                  <input
                    value={compareHead}
                    onChange={(e) => setCompareHead(e.target.value)}
                    placeholder="feature/coupon-cap"
                  />
                </label>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={importDiffFromRepo}
                  disabled={diffImporting}
                >
                  {diffImporting ? 'Fetching diff...' : 'Import diff into form'}
                </button>
                {diffImportNote && <p className="diff-import-note muted">{diffImportNote}</p>}
                {codeDiffs.trim() && (
                  <p className="diff-import-note muted">
                    Diff loaded ({codeDiffs.split('\n').length} lines).
                  </p>
                )}
              </div>
            )}

            {diffMode === 'fetch' && !isGithubFetchReady(repoConnection) && (
              <div className="diff-fetch-setup banner banner-warn">
                <p>
                  <strong>From GitHub</strong> requires a repository and personal access token.
                </p>
                <p className="muted">
                  Add owner, repo, and PAT in{' '}
                  <Link to="/settings">Settings</Link>, then return here to import a diff.
                </p>
              </div>
            )}
          </div>
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
