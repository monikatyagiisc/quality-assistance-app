import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type JiraConnectionStatus, type RepositoryConnection } from '../api/client'
import { useAuth } from '../context/useAuth'
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
  const [, setSearchParams] = useSearchParams()
  const [jiraCallbackResult] = useState(() =>
    new URLSearchParams(window.location.search).get('jira'),
  )
  const [entraCallbackResult] = useState(() =>
    new URLSearchParams(window.location.search).get('entra'),
  )
  const [connection, setConnection] = useState<RepositoryConnection | null>(null)
  const [jiraConnection, setJiraConnection] = useState<JiraConnectionStatus | null>(null)
  const [entraAccount, setEntraAccount] = useState<{ enabled: boolean; linked: boolean } | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [loadingExisting, setLoadingExisting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [jiraSaving, setJiraSaving] = useState(false)
  const [entraSaving, setEntraSaving] = useState(false)
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
        const jiraData = await api.getJiraStatus(token)
        setJiraConnection(jiraData)
        const entraData = await api.getEntraAccount(token)
        setEntraAccount(entraData)
      } catch (err) {
        setError(getUserFriendlyError(err))
      } finally {
        setLoadingExisting(false)
      }
    }

    void load()
  }, [token, authLoading])

  useEffect(() => {
    if (!jiraCallbackResult) return

    if (jiraCallbackResult === 'connected' && token) {
      void api.getJiraStatus(token).then(setJiraConnection).catch((err) => {
        setError(getUserFriendlyError(err))
      })
    }

    const nextParams = new URLSearchParams(window.location.search)
    nextParams.delete('jira')
    setSearchParams(nextParams, { replace: true })
  }, [jiraCallbackResult, setSearchParams, token])

  useEffect(() => {
    if (!entraCallbackResult) return

    if (entraCallbackResult === 'linked' && token) {
      void api.getEntraAccount(token).then(setEntraAccount).catch((err) => {
        setError(getUserFriendlyError(err))
      })
    }

    const nextParams = new URLSearchParams(window.location.search)
    nextParams.delete('entra')
    setSearchParams(nextParams, { replace: true })
  }, [entraCallbackResult, setSearchParams, token])

  const handleEntraLink = async () => {
    if (!token) return
    setEntraSaving(true)
    setError(null)
    try {
      const { authorization_url } = await api.startEntraLink(token)
      window.location.assign(authorization_url)
    } catch (err) {
      setError(getUserFriendlyError(err))
      setEntraSaving(false)
    }
  }

  const handleJiraConnect = async () => {
    if (!token) return
    setJiraSaving(true)
    setError(null)
    try {
      const { authorization_url } = await api.startJiraConnection(token)
      window.location.assign(authorization_url)
    } catch (err) {
      setError(getUserFriendlyError(err))
      setJiraSaving(false)
    }
  }

  const handleJiraDisconnect = async () => {
    if (!token || !window.confirm('Disconnect Jira and remove its saved authorization?')) return
    setJiraSaving(true)
    setError(null)
    try {
      await api.disconnectJira(token)
      setJiraConnection((current) =>
        current ? { ...current, connected: false, site_name: null, site_url: null } : current,
      )
      setMessage('Jira disconnected.')
    } catch (err) {
      setError(getUserFriendlyError(err))
    } finally {
      setJiraSaving(false)
    }
  }

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
          Connect GitHub to import code changes or Jira Cloud to load your assigned user stories.
          OAuth tokens are encrypted at rest and used only by the backend.
        </p>
      </header>

      <section className="panel settings-panel jira-settings-panel">
        <div className="settings-panel-title">
          <h2>Jira Cloud</h2>
          {jiraConnection?.connected && (
            <span className="connection-status-badge">Connected</span>
          )}
        </div>
        {jiraConnection?.configured ? (
          <>
            <p className="field-hint">
              Authorize with your company Atlassian account to select issues assigned to you. Only
              issue details needed for the workspace are fetched.
            </p>
            {jiraConnection.connected && jiraConnection.site_name && (
              <p className="connection-status">
                Connected site:{' '}
                <a href={jiraConnection.site_url ?? undefined} target="_blank" rel="noreferrer">
                  {jiraConnection.site_name}
                </a>
              </p>
            )}
            <div className="settings-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleJiraConnect}
                disabled={jiraSaving || !token}
              >
                {jiraSaving ? 'Opening Atlassian...' : jiraConnection.connected ? 'Reconnect Jira' : 'Connect Jira'}
              </button>
              {jiraConnection.connected && (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={handleJiraDisconnect}
                  disabled={jiraSaving}
                >
                  Disconnect
                </button>
              )}
            </div>
          </>
        ) : (
          <p className="field-hint">
            Jira OAuth is not configured by the application administrator yet.
          </p>
        )}
      </section>

      <section className="panel settings-panel">
        <div className="settings-panel-title">
          <h2>Microsoft Entra ID</h2>
          {entraAccount?.linked && (
            <span className="connection-status-badge">Linked</span>
          )}
        </div>
        {entraAccount?.enabled ? (
          <>
            <p className="field-hint">
              Link the Microsoft account with the same email as this app account. This one-time step
              lets you use company SSO on future sign-ins.
            </p>
            <div className="settings-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleEntraLink}
                disabled={entraSaving || entraAccount.linked || !token}
              >
                {entraSaving ? 'Opening Microsoft...' : entraAccount.linked ? 'Microsoft linked' : 'Link Microsoft account'}
              </button>
            </div>
          </>
        ) : (
          <p className="field-hint">
            Microsoft Entra SSO is not configured by the application administrator yet.
          </p>
        )}
      </section>

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
      {jiraCallbackResult === 'connected' && (
        <div className="banner banner-success">Jira Cloud connected successfully.</div>
      )}
      {jiraCallbackResult === 'cancelled' && (
        <div className="banner banner-success">Jira connection was cancelled.</div>
      )}
      {jiraCallbackResult === 'error' && (
        <div className="banner banner-error">
          Could not connect Jira. Check the OAuth app configuration and try again.
        </div>
      )}
      {jiraCallbackResult === 'site-selection' && (
        <div className="banner banner-error">
          Multiple Jira sites were authorized. Reconnect and select only your office Jira site.
        </div>
      )}
      {entraCallbackResult === 'linked' && (
        <div className="banner banner-success">Microsoft account linked successfully.</div>
      )}
      {entraCallbackResult === 'error' && (
        <div className="banner banner-error">
          Could not link Microsoft. Confirm the email matches your app account and try again.
        </div>
      )}

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
