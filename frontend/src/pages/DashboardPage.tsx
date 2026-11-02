import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  api,
  type AssistanceAgent,
  type AssistanceResult,
  type JiraCreatedIssue,
  type JiraConnectionStatus,
  type JiraIssue,
  type JiraProject,
  type RepositoryConnection,
} from '../api/client'
import { getUserFriendlyError } from '../utils/errorMessages'
import { ASSISTANCE_SAMPLES } from '../data/assistanceSamples'
import { useAuth } from '../context/useAuth'
import { SettingsInfoLink } from '../components/SettingsInfoLink'
import { ThinkingIndicator } from '../components/ThinkingIndicator'
import { MarkdownContent } from '../components/MarkdownContent'
import { extractBugReports } from '../utils/bugReports'
import './DashboardPage.css'

const DIFF_SETTINGS_REQUIRED_MSG =
  'Code diffs require a saved GitHub repository and PAT. Add them in Settings before pasting.'

const SPECIALIST_OPTIONS: { value: AssistanceAgent; label: string }[] = [
  { value: 'test_case_generation', label: 'Test Case Generation' },
  { value: 'test_data_generation', label: 'Test Data Generation' },
  { value: 'test_script_automation', label: 'Test Script Automation' },
  { value: 'test_execution', label: 'Test Execution' },
  { value: 'self_healing_test_scripts', label: 'Self-Healing Test Scripts' },
  { value: 'change_impact_analysis', label: 'Change Impact Analysis' },
  { value: 'bug_report_generation', label: 'Bug Report Generation' },
  { value: 'test_summary_reporting', label: 'Test Summary Reporting' },
  { value: 'release_readiness_evaluation', label: 'Release Readiness Evaluation' },
]

function isGithubFetchReady(
  connection: RepositoryConnection | null,
): connection is RepositoryConnection {
  return Boolean(connection?.owner && connection?.repo && connection.has_token)
}

function canAcceptCodeDiffs(connection: RepositoryConnection | null, value: string): boolean {
  return !value.trim() || isGithubFetchReady(connection)
}

function downloadResultMarkdown(content: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `quality-assistance-${new Date().toISOString().slice(0, 10)}.md`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function downloadResultHtml(content: string) {
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quality Assistance Results</title>
  <style>
    body { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; color: #1f2937; font: 16px/1.6 system-ui, sans-serif; }
    h1, h2, h3, h4 { line-height: 1.3; margin: 1.5rem 0 0.75rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    th, td { border: 1px solid #cbd5e1; padding: 0.5rem 0.65rem; text-align: left; }
    th { background: #f1f5f9; }
    code { padding: 0.1rem 0.3rem; background: #f1f5f9; border-radius: 0.25rem; }
    pre { overflow-x: auto; padding: 1rem; background: #f1f5f9; border-radius: 0.5rem; }
    blockquote { margin-left: 0; padding-left: 1rem; border-left: 3px solid #94a3b8; color: #475569; }
    img { max-width: 100%; }
    @media print { body { max-width: none; margin: 0; } }
  </style>
</head>
<body>
  <main>${content}</main>
</body>
</html>`
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `quality-assistance-${new Date().toISOString().slice(0, 10)}.html`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function DashboardPage() {
  const { token, user } = useAuth()
  const [activeTab, setActiveTab] = useState<'input' | 'results'>('input')
  const [requirements, setRequirements] = useState('')
  const [userStories, setUserStories] = useState('')
  const [codeDiffs, setCodeDiffs] = useState('')
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingStartedAt, setLoadingStartedAt] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AssistanceResult | null>(null)
  const [humanGuidance, setHumanGuidance] = useState('')
  const [targetAgent, setTargetAgent] = useState<AssistanceAgent | 'all'>('all')
  const [repoConnection, setRepoConnection] = useState<RepositoryConnection | null>(null)
  const [jiraConnection, setJiraConnection] = useState<JiraConnectionStatus | null>(null)
  const [jiraIssues, setJiraIssues] = useState<JiraIssue[]>([])
  const [jiraNextPageToken, setJiraNextPageToken] = useState<string | null>(null)
  const [selectedJiraIssue, setSelectedJiraIssue] = useState<JiraIssue | null>(null)
  const [jiraIssuesLoaded, setJiraIssuesLoaded] = useState(false)
  const [jiraError, setJiraError] = useState<string | null>(null)
  const [jiraLoading, setJiraLoading] = useState(false)
  const [jiraDetailLoading, setJiraDetailLoading] = useState(false)
  const [jiraBugPanelOpen, setJiraBugPanelOpen] = useState(false)
  const [jiraProjects, setJiraProjects] = useState<JiraProject[]>([])
  const [jiraProjectsLoading, setJiraProjectsLoading] = useState(false)
  const [jiraProjectsError, setJiraProjectsError] = useState<string | null>(null)
  const [jiraProjectKey, setJiraProjectKey] = useState('')
  const [selectedBugIds, setSelectedBugIds] = useState<string[]>([])
  const [jiraCreatingBugs, setJiraCreatingBugs] = useState(false)
  const [jiraCreateError, setJiraCreateError] = useState<string | null>(null)
  const [createdJiraBugs, setCreatedJiraBugs] = useState<
    Array<{ bugId: string; issue: JiraCreatedIssue }>
  >([])
  const [diffMode, setDiffMode] = useState<'paste' | 'fetch'>('paste')
  const [pullNumber, setPullNumber] = useState('')
  const [compareHead, setCompareHead] = useState('')
  const [diffImporting, setDiffImporting] = useState(false)
  const [diffImportNote, setDiffImportNote] = useState<string | null>(null)
  const resultContentRef = useRef<HTMLDivElement>(null)
  const jiraSelectionRef = useRef(0)

  const selectedSample = ASSISTANCE_SAMPLES.find((s) => s.id === selectedSampleId)
  const bugReports = useMemo(
    () => (result ? extractBugReports(result.response) : []),
    [result],
  )

  useEffect(() => {
    if (!token) return
    void api.getRepositorySettings(token).then(setRepoConnection).catch(() => setRepoConnection(null))
    void api.getJiraStatus(token).then(setJiraConnection).catch((err) => {
      setError(getUserFriendlyError(err))
    })
  }, [token])

  const loadJiraIssues = async (nextPageToken?: string | null) => {
    if (!token) return
    setJiraLoading(true)
    setJiraError(null)
    try {
      const page = await api.getAssignedJiraIssues(token, nextPageToken)
      setJiraIssues((current) => (nextPageToken ? [...current, ...page.issues] : page.issues))
      setJiraNextPageToken(page.next_page_token)
      setJiraIssuesLoaded(true)
    } catch (err) {
      setJiraError(getUserFriendlyError(err))
    } finally {
      setJiraLoading(false)
    }
  }

  const selectJiraIssue = async (issueKey: string) => {
    const selection = ++jiraSelectionRef.current
    const issue = jiraIssues.find((candidate) => candidate.key === issueKey) ?? null
    if (!issue || !token) {
      setSelectedJiraIssue(null)
      setJiraDetailLoading(false)
      return
    }

    setSelectedJiraIssue(issue)
    setJiraDetailLoading(true)
    setJiraError(null)
    setUserStories(`${issue.key}: ${issue.summary}`)
    setSelectedSampleId(null)
    try {
      const details = await api.getJiraIssue(token, issue.key)
      if (selection !== jiraSelectionRef.current) return
      setSelectedJiraIssue(details)
      setUserStories(
        `${details.key}: ${details.summary}${details.description ? `\n\n${details.description}` : ''}`,
      )
    } catch (err) {
      if (selection === jiraSelectionRef.current) setJiraError(getUserFriendlyError(err))
    } finally {
      if (selection === jiraSelectionRef.current) setJiraDetailLoading(false)
    }
  }

  const loadJiraProjects = async () => {
    if (!token) return
    setJiraProjectsLoading(true)
    setJiraProjectsError(null)
    try {
      const response = await api.getJiraProjects(token)
      setJiraProjects(response.projects)
      setJiraProjectKey((current) =>
        response.projects.some((project) => project.key === current)
          ? current
          : '',
      )
    } catch (err) {
      setJiraProjectsError(getUserFriendlyError(err))
    } finally {
      setJiraProjectsLoading(false)
    }
  }

  const toggleJiraBugPanel = () => {
    const opening = !jiraBugPanelOpen
    setJiraBugPanelOpen(opening)
    setJiraCreateError(null)
    if (opening && jiraConnection?.connected && jiraProjects.length === 0) {
      void loadJiraProjects()
    }
  }

  const createJiraBugs = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token || !jiraProjectKey || selectedBugIds.length === 0) return
    const selectedBugs = bugReports.filter((bug) => selectedBugIds.includes(bug.id))
    setJiraCreatingBugs(true)
    setJiraCreateError(null)
    const outcomes = await Promise.allSettled(
      selectedBugs.map((bug) =>
        api.createJiraIssue(token, {
          project_key: jiraProjectKey,
          summary: bug.title,
          description: bug.description,
        }),
      ),
    )
    const created = outcomes.flatMap((outcome, index) =>
      outcome.status === 'fulfilled'
        ? [{ bugId: selectedBugs[index].id, issue: outcome.value }]
        : [],
    )
    const failures = outcomes.flatMap((outcome, index) =>
      outcome.status === 'rejected'
        ? [`${selectedBugs[index].title}: ${getUserFriendlyError(outcome.reason)}`]
        : [],
    )
    setCreatedJiraBugs((current) => [...current, ...created])
    setSelectedBugIds((current) => current.filter((id) => !created.some((bug) => bug.bugId === id)))
    if (failures.length) {
      setJiraCreateError(
        `${created.length} Jira bug${created.length === 1 ? '' : 's'} created. ${failures.join(' ')}`,
      )
    }
    setJiraCreatingBugs(false)
  }

  const resetJiraBugCreation = () => {
    setJiraBugPanelOpen(false)
    setSelectedBugIds([])
    setJiraCreateError(null)
    setCreatedJiraBugs([])
  }

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
      resetJiraBugCreation()
      setResult(null)
    }
  }

  const clearForm = () => {
    setSelectedSampleId(null)
    setRequirements('')
    setUserStories('')
    setCodeDiffs('')
    setHumanGuidance('')
    setTargetAgent('all')
    setError(null)
    resetJiraBugCreation()
    setResult(null)
  }

  const runAssistance = async (
    guidance?: string,
    specialist?: AssistanceAgent,
    preservePreviousResult = true,
  ) => {
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

    if (!preservePreviousResult) {
      resetJiraBugCreation()
      setResult(null)
    }
    setLoading(true)
    setActiveTab('results')
    setLoadingStartedAt(Date.now())
    setError(null)

    try {
      const data = await api.assist(token, {
        requirements,
        user_stories: userStories || null,
        code_diffs: codeDiffs || null,
        session_id: sessionId,
        human_guidance: guidance?.trim() || null,
        target_agent: specialist ?? null,
      })
      resetJiraBugCreation()
      setResult(data)
      setSessionId(data.session_id)
    } catch (err) {
      setError(getUserFriendlyError(err))
    } finally {
      setLoading(false)
      setLoadingStartedAt(null)
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await runAssistance(
      undefined,
      targetAgent === 'all' ? undefined : targetAgent,
      false,
    )
  }

  const handleRerun = async (event: FormEvent) => {
    event.preventDefault()
    await runAssistance(humanGuidance, targetAgent === 'all' ? undefined : targetAgent)
  }

  const startNewSession = () => {
    setSessionId(null)
    resetJiraBugCreation()
    setResult(null)
    setHumanGuidance('')
    setTargetAgent('all')
    setError(null)
    setSelectedSampleId(null)
    setActiveTab('input')
  }

  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const tabs = ['input', 'results'] as const
    const currentIndex = tabs.indexOf(activeTab)
    let nextIndex: number

    if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % tabs.length
    else if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + tabs.length) % tabs.length
    else if (event.key === 'Home') nextIndex = 0
    else if (event.key === 'End') nextIndex = tabs.length - 1
    else return

    event.preventDefault()
    const nextTab = tabs[nextIndex]
    setActiveTab(nextTab)
    document.getElementById(`dashboard-tab-${nextTab}`)?.focus()
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

      <div className="dashboard-tabs" role="tablist" aria-label="Quality assistance workspace">
        <button
          id="dashboard-tab-input"
          type="button"
          role="tab"
          aria-selected={activeTab === 'input'}
          aria-controls="dashboard-panel-input"
          tabIndex={activeTab === 'input' ? 0 : -1}
          className={`dashboard-tab${activeTab === 'input' ? ' active' : ''}`}
          onClick={() => setActiveTab('input')}
          onKeyDown={handleTabKeyDown}
        >
          Input
        </button>
        <button
          id="dashboard-tab-results"
          type="button"
          role="tab"
          aria-selected={activeTab === 'results'}
          aria-controls="dashboard-panel-results"
          tabIndex={activeTab === 'results' ? 0 : -1}
          className={`dashboard-tab${activeTab === 'results' ? ' active' : ''}`}
          onClick={() => setActiveTab('results')}
          onKeyDown={handleTabKeyDown}
        >
          Results
          {result && <span className="dashboard-tab-indicator" aria-label="Result available" />}
        </button>
      </div>

      <div className="dashboard-grid">
        {activeTab === 'input' && (
          <form
            id="dashboard-panel-input"
            className="panel input-panel"
            role="tabpanel"
            aria-labelledby="dashboard-tab-input"
            tabIndex={0}
            onSubmit={handleSubmit}
          >
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
          <div className="jira-issue-picker">
            <div className="jira-issue-picker-header">
              <span>Import an assigned Jira issue</span>
              {jiraConnection?.connected ? (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => void loadJiraIssues()}
                  disabled={jiraLoading}
                >
                  {jiraLoading
                    ? 'Loading issues…'
                    : jiraIssuesLoaded
                      ? 'Refresh assigned issues'
                      : 'Load assigned issues'}
                </button>
              ) : (
                <Link to="/settings">Connect Jira in Settings</Link>
              )}
            </div>
            {jiraConnection?.connected && (
              <>
                {jiraError && <div className="banner banner-error" role="alert">{jiraError}</div>}
                <label className="jira-issue-select-label">
                  Assigned issue
                  <select
                    value={selectedJiraIssue?.key ?? ''}
                    onChange={(event) => void selectJiraIssue(event.target.value)}
                    disabled={jiraLoading || jiraIssues.length === 0}
                  >
                    <option value="">
                      {jiraIssues.length
                        ? 'Select an issue…'
                        : jiraIssuesLoaded
                          ? 'No assigned issues available'
                          : 'Load assigned issues first'}
                    </option>
                    {jiraIssues.map((issue) => (
                      <option key={issue.id} value={issue.key}>
                        {issue.key} — {issue.summary}
                      </option>
                    ))}
                  </select>
                </label>
                {jiraIssuesLoaded && jiraIssues.length === 0 && !jiraError && (
                  <p className="muted">Jira did not return any issues assigned to your account.</p>
                )}
                {jiraNextPageToken && (
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm jira-more-button"
                    onClick={() => void loadJiraIssues(jiraNextPageToken)}
                    disabled={jiraLoading}
                  >
                    {jiraLoading ? 'Loading…' : 'Load more issues'}
                  </button>
                )}
                {selectedJiraIssue && (
                  <div className="jira-issue-preview" aria-live="polite">
                    <div className="jira-issue-preview-heading">
                      <strong>{selectedJiraIssue.key}: {selectedJiraIssue.summary}</strong>
                      <span>
                        {[selectedJiraIssue.issue_type, selectedJiraIssue.status]
                          .filter(Boolean)
                          .join(' · ')}
                      </span>
                    </div>
                    <p>
                      {jiraDetailLoading
                        ? 'Loading issue description…'
                        : selectedJiraIssue.description || 'This Jira issue has no description.'}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
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
          <label>
            Analysis scope
            <select
              value={targetAgent}
              onChange={(event) => {
                const selected = event.target.value
                setTargetAgent(
                  selected === 'all'
                    ? 'all'
                    : SPECIALIST_OPTIONS.find((specialist) => specialist.value === selected)
                        ?.value ?? 'all',
                )
              }}
              disabled={loading}
            >
              <option value="all">Full quality review</option>
              {SPECIALIST_OPTIONS.map((specialist) => (
                <option key={specialist.value} value={specialist.value}>
                  {specialist.label}
                </option>
              ))}
            </select>
            <span className="muted">
              Choose a specialist to focus this run, or leave the full review selected.
            </span>
          </label>
          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading || !requirements.trim()}
          >
            {loading ? 'Running quality assistance...' : 'Get quality assistance'}
          </button>
          </form>
        )}

        {activeTab === 'results' && (
          <section
            id="dashboard-panel-results"
            className="panel output-panel"
            role="tabpanel"
            aria-labelledby="dashboard-tab-results"
            tabIndex={0}
          >
          <h2>Results</h2>
          {error && <div className="banner banner-error">{error}</div>}
          {!error && !result && !loading && (
            <p className="muted">Submit requirements or load a sample to generate QA guidance.</p>
          )}
          {loading && loadingStartedAt !== null && (
            <ThinkingIndicator startedAt={loadingStartedAt} />
          )}
          {result && (
            <article className="result">
              <div className="result-meta">
                <span className={`badge badge-${result.status}`}>{result.status}</span>
                <span>Session: {result.session_id}</span>
                <div className="result-downloads" role="group" aria-label="Download results">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm result-download"
                    onClick={() => downloadResultMarkdown(result.response)}
                  >
                    Markdown
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm result-download"
                    onClick={() => {
                      const renderedResult = resultContentRef.current?.innerHTML
                      if (renderedResult) downloadResultHtml(renderedResult)
                    }}
                  >
                    HTML
                  </button>
                </div>
              </div>
              <div ref={resultContentRef}>
                <MarkdownContent content={result.response} />
              </div>
              {bugReports.length > 0 && (
                <section className="jira-bug-creation" aria-labelledby="jira-bug-creation-title">
                  <div className="jira-bug-creation-header">
                    <div>
                      <h3 id="jira-bug-creation-title">Create Jira tickets for bugs</h3>
                      <p className="muted">
                        Select the bug reports to create as Bug issues in one Jira project.
                      </p>
                    </div>
                    {jiraConnection?.connected ? (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={toggleJiraBugPanel}
                      >
                        {jiraBugPanelOpen ? 'Close' : 'Create Jira tickets'}
                      </button>
                    ) : (
                      <Link to="/settings">Connect Jira in Settings</Link>
                    )}
                  </div>
                  {jiraBugPanelOpen && jiraConnection?.connected && (
                    <form className="jira-bug-form" onSubmit={(event) => void createJiraBugs(event)}>
                      {jiraProjectsError && (
                        <div className="banner banner-error" role="alert">{jiraProjectsError}</div>
                      )}
                      {jiraCreateError && (
                        <div className="banner banner-error" role="alert">{jiraCreateError}</div>
                      )}
                      <label className="jira-issue-select-label">
                        Jira project
                        <select
                          value={jiraProjectKey}
                          onChange={(event) => setJiraProjectKey(event.target.value)}
                          disabled={jiraProjectsLoading || jiraProjects.length === 0}
                          required
                        >
                          <option value="">
                            {jiraProjectsLoading
                              ? 'Loading projects…'
                              : jiraProjects.length
                                ? 'Select a project…'
                                : 'No projects available'}
                          </option>
                          {jiraProjects.map((project) => (
                            <option key={project.id} value={project.key}>
                              {project.name} ({project.key})
                            </option>
                          ))}
                        </select>
                      </label>
                      {jiraProjects.length === 0 && !jiraProjectsLoading && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => void loadJiraProjects()}
                        >
                          Retry loading projects
                        </button>
                      )}
                      <fieldset className="jira-bug-options">
                        <legend>Select bug reports</legend>
                        {bugReports.map((bug) => {
                          const alreadyCreated = createdJiraBugs.some((entry) => entry.bugId === bug.id)
                          return (
                            <label key={bug.id} className="jira-bug-option">
                              <input
                                type="checkbox"
                                checked={selectedBugIds.includes(bug.id)}
                                disabled={alreadyCreated || jiraCreatingBugs}
                                onChange={(event) => {
                                  setSelectedBugIds((current) =>
                                    event.target.checked
                                      ? [...current, bug.id]
                                      : current.filter((id) => id !== bug.id),
                                  )
                                }}
                              />
                              <span>
                                <strong>{bug.title}</strong>
                                {alreadyCreated && <span className="muted"> · created</span>}
                              </span>
                            </label>
                          )
                        })}
                      </fieldset>
                      <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={
                          jiraCreatingBugs ||
                          jiraProjectsLoading ||
                          !jiraProjectKey ||
                          selectedBugIds.length === 0
                        }
                      >
                        {jiraCreatingBugs ? 'Creating Jira bugs…' : 'Create selected bugs'}
                      </button>
                    </form>
                  )}
                  {createdJiraBugs.length > 0 && (
                    <div className="jira-created-bugs" aria-live="polite">
                      <h4>Created Jira bugs</h4>
                      <ul>
                        {createdJiraBugs.map(({ issue }) => (
                          <li key={issue.id}>
                            <a href={issue.url} target="_blank" rel="noreferrer">
                              {issue.key}: {issue.summary}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </section>
              )}
            </article>
          )}
          {result && (
            <form className="result-refinement" onSubmit={handleRerun}>
              <h3>Refine and rerun</h3>
              <p className="muted">
                Keep the current requirements, story, and code context. Add review instructions
                or focus the rerun on one specialist.
              </p>
              <label>
                Human review instructions (optional)
                <textarea
                  value={humanGuidance}
                  onChange={(event) => setHumanGuidance(event.target.value)}
                  rows={4}
                  maxLength={5000}
                  placeholder="For example: Add negative cases for expired sessions and prioritize high-risk scenarios."
                  disabled={loading}
                />
              </label>
              <label>
                Rerun scope
                <select
                  value={targetAgent}
                  onChange={(event) => {
                    const selected = event.target.value
                    setTargetAgent(
                      selected === 'all'
                        ? 'all'
                        : SPECIALIST_OPTIONS.find((specialist) => specialist.value === selected)
                            ?.value ?? 'all',
                    )
                  }}
                  disabled={loading}
                >
                  <option value="all">Full quality review</option>
                  {SPECIALIST_OPTIONS.map((specialist) => (
                    <option key={specialist.value} value={specialist.value}>
                      {specialist.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !requirements.trim()}
              >
                {loading ? 'Rerunning…' : 'Rerun assistance'}
              </button>
            </form>
          )}
          </section>
        )}
      </div>
    </div>
  )
}
