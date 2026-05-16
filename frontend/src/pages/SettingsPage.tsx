import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, type RepositoryConnection } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { getUserFriendlyError } from '../utils/errorMessages'
import './SettingsPage.css'

const EMPTY_FORM = {
  owner: '',
  repo: '',
  default_branch: 'main',
  access_token: '',
}

export function SettingsPage() {
  const { token, loading: authLoading } = useAuth()
  const [connection, setConnection] = useState<RepositoryConnection | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [loadingExisting, setLoadingExisting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (authLoading || !token) return

    const load = async () => {
      setLoadingExisting(true)
      setError(null)
      try {
        const data = await api.getRepositorySettings(token)
        setConnection(data ?? null)
        if (data) {
          setForm({
            owner: data.owner,
            repo: data.repo,
            default_branch: data.default_branch,
            access_token: '',
          })
        }
      } catch (err) {
        setError(getUserFriendlyError(err))
      } finally {
        setLoadingExisting(false)
      }
    }

    void load()
  }, [token, authLoading])

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return

    if (!connection?.has_token && !form.access_token.trim()) {
      setError('Personal access token is required to use From GitHub.')
      return
    }

    setSaving(true)
    setError(null)
    setMessage(null)

    try {
      const saved = await api.saveRepositorySettings(token, {
        provider: 'github',
        owner: form.owner,
        repo: form.repo,
        default_branch: form.default_branch,
        access_token: form.access_token || null,
      })
      setConnection(saved)
      setForm((prev) => ({ ...prev, access_token: '' }))
      setMessage('Repository settings saved.')
    } catch (err) {
      setError(getUserFriendlyError(err))
    } finally {
      setSaving(false)
    }
  }

  const handleRemove = async () => {
    if (!token) return
    if (!window.confirm('Remove repository connection and stored token?')) return

    setSaving(true)
    setError(null)
    setMessage(null)

    try {
      await api.deleteRepositorySettings(token)
      setConnection(null)
      setForm(EMPTY_FORM)
      setMessage('Repository connection removed.')
    } catch (err) {
      setError(getUserFriendlyError(err))
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) {
    return (
      <div className="settings">
        <p className="muted">Loading...</p>
      </div>
    )
  }

  return (
    <div className="settings">
      <header className="settings-hero">
        <p className="eyebrow">Configuration</p>
        <h1>Settings</h1>
        <p className="settings-lead">
          Connect a GitHub repository so the workspace can pull unified diffs for change-impact
          analysis. Tokens are encrypted at rest and only used on the server — the agent never
          receives your credentials.
        </p>
      </header>

      <section className="panel settings-panel">
        <h2>How code diffs reach the agent</h2>
        <ol className="settings-steps">
          <li>
            <strong>Paste (default)</strong> — Copy output from <code>git diff</code> into the
            workspace. No repository access is required.
          </li>
          <li>
            <strong>Fetch from GitHub</strong> — Save owner/repo and a PAT below, then import a PR
            or branch compare on the <Link to="/dashboard">workspace</Link>.
          </li>
          <li>
            <strong>Analysis</strong> — The diff text is sent to the Change Impact Analysis agent
            with your requirements; only the diff content leaves this app, not clone access.
          </li>
        </ol>
      </section>

      {error && <div className="banner banner-error">{error}</div>}
      {message && <div className="banner banner-success">{message}</div>}

      <section className="panel settings-panel">
        <div className="settings-panel-title">
          <h2>GitHub repository</h2>
          {loadingExisting && <span className="muted settings-loading-badge">Refreshing…</span>}
        </div>

        <form className="settings-form" onSubmit={handleSave}>
          <div className="form-row">
            <label>
              Owner / organization
              <input
                value={form.owner}
                onChange={(e) => setForm({ ...form, owner: e.target.value })}
                placeholder="acme-corp"
                required
              />
            </label>
            <label>
              Repository name
              <input
                value={form.repo}
                onChange={(e) => setForm({ ...form, repo: e.target.value })}
                placeholder="payments-service"
                required
              />
            </label>
          </div>

          <label>
            Default base branch
            <input
              value={form.default_branch}
              onChange={(e) => setForm({ ...form, default_branch: e.target.value })}
              placeholder="main"
              required
            />
          </label>

            <label>
              GitHub personal access token
              {!connection?.has_token && <span className="required-mark">*</span>}
              <input
                type="password"
                value={form.access_token}
                onChange={(e) => setForm({ ...form, access_token: e.target.value })}
                placeholder={
                  connection?.has_token
                    ? 'Token saved — enter a new value to replace'
                    : 'ghp_... (required)'
                }
                autoComplete="off"
                required={!connection?.has_token}
              />
            </label>
            <p className="field-hint">
              Required for <strong>From GitHub</strong> on the workspace. Use a PAT with{' '}
              <strong>Contents: Read</strong> and <strong>Pull requests: Read</strong>.
            </p>

          {connection && (
            <p className="connection-status">
              Saved: <strong>{connection.repo_label}</strong>
              {connection.has_token ? ' · token on file' : ' · no token (public only)'}
            </p>
          )}

          <div className="settings-actions">
            <button type="submit" className="btn btn-primary" disabled={saving || !token}>
              {saving ? 'Saving...' : connection ? 'Update repository' : 'Save repository'}
            </button>
            {connection && (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleRemove}
                disabled={saving}
              >
                Remove connection
              </button>
            )}
          </div>
        </form>
      </section>
    </div>
  )
}
