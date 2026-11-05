const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type User = {
  id: string
  email: string
  full_name: string
  created_at: string
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: User
}

export type RepositoryConnection = {
  provider: string
  owner: string
  repo: string
  default_branch: string
  has_token: boolean
  repo_label: string
}

export type FetchDiffResult = {
  diff: string
  source: string
  summary: string
}

export type GitHubPullRequest = {
  number: number
  title: string
  head_ref: string
  base_ref: string
  state: string
}

export type JiraConnectionStatus = {
  configured: boolean
  connected: boolean
  site_name: string | null
  site_url: string | null
}

export type JiraIssue = {
  id: string
  key: string
  summary: string
  description: string
  issue_type: string | null
  status: string | null
}

export type JiraIssuePage = {
  issues: JiraIssue[]
  next_page_token: string | null
}

export type JiraProject = {
  id: string
  key: string
  name: string
}

export type JiraCreatedIssue = {
  id: string
  key: string
  summary: string
  url: string
}

export type AssistanceResult = {
  id: string
  session_id: string
  response: string
  status: string
  created_at: string
}

export type AssistanceAgent =
  | 'test_case_generation'
  | 'test_data_generation'
  | 'test_script_automation'
  | 'test_execution'
  | 'self_healing_test_scripts'
  | 'change_impact_analysis'
  | 'bug_report_generation'
  | 'test_summary_reporting'
  | 'release_readiness_evaluation'

type ErrorDetailObject = {
  message?: string
  code?: string
  detail?: string
}

class ApiError extends Error {
  status: number
  code?: string

  constructor(status: number, message: string, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

function parseErrorDetail(body: unknown): { message: string; code?: string } {
  if (!body || typeof body !== 'object') {
    return { message: 'Request failed' }
  }

  const record = body as { detail?: string | ErrorDetailObject }
  const { detail } = record

  if (typeof detail === 'string') {
    return { message: detail }
  }

  if (detail && typeof detail === 'object') {
    return {
      message: detail.message || detail.detail || 'Request failed',
      code: detail.code,
    }
  }

  return { message: 'Request failed' }
}

const DEFAULT_REQUEST_TIMEOUT_MS = 15_000
const ASSIST_REQUEST_TIMEOUT_MS = 180_000

type RequestOptions = {
  timeoutMs?: number
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
  requestOptions: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const timeoutMs = requestOptions.timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      const isAssist = path === '/api/assist'
      throw new ApiError(
        0,
        isAssist
          ? 'Quality assistance is taking longer than expected. The agent may still be working — wait a moment and try again if no result appears.'
          : 'Request timed out. Is the backend running on ' + API_URL + '?',
        isAssist ? 'assist_timeout' : 'timeout',
      )
    }
    throw new ApiError(
      0,
      'Cannot reach the API. Start the backend (port 8000) and try again.',
      'network',
    )
  } finally {
    window.clearTimeout(timeoutId)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const { message, code } = parseErrorDetail(body)
    throw new ApiError(response.status, message, code)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const api = {
  register: (data: { email: string; password: string; full_name: string }) =>
    request<AuthResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }),

  getEntraSsoStatus: () => request<{ enabled: boolean }>('/api/auth/entra/status'),

  startEntraSignIn: () =>
    request<{ authorization_url: string }>('/api/auth/entra/start', { method: 'POST' }),

  getEntraAccount: (token: string) =>
    request<{ enabled: boolean; linked: boolean }>('/api/auth/entra/account', {}, token),

  startEntraLink: (token: string) =>
    request<{ authorization_url: string }>(
      '/api/auth/entra/link/start',
      { method: 'POST' },
      token,
    ),

  exchangeEntraTicket: (ticket: string) =>
    request<AuthResponse>(
      '/api/auth/entra/exchange',
      { method: 'POST', body: JSON.stringify({ ticket }) },
    ),

  me: (token: string) => request<User>('/api/auth/me', {}, token),

  assist: (
    token: string,
    data: {
      requirements: string
      user_stories?: string | null
      code_diffs?: string | null
      session_id?: string | null
      human_guidance?: string | null
      target_agent?: AssistanceAgent | null
    },
  ) =>
    request<AssistanceResult>(
      '/api/assist',
      { method: 'POST', body: JSON.stringify(data) },
      token,
      { timeoutMs: ASSIST_REQUEST_TIMEOUT_MS },
    ),

  getRepositorySettings: async (token: string) => {
    const result = await request<RepositoryConnection | null>('/api/settings/repository', {}, token)
    return result ?? null
  },

  saveRepositorySettings: (
    token: string,
    data: {
      provider?: string
      owner: string
      repo: string
      default_branch: string
      access_token?: string | null
    },
  ) =>
    request<RepositoryConnection>(
      '/api/settings/repository',
      { method: 'PUT', body: JSON.stringify(data) },
      token,
    ),

  deleteRepositorySettings: (token: string) =>
    request<void>('/api/settings/repository', { method: 'DELETE' }, token),

  fetchRepositoryDiff: (
    token: string,
    data: { base?: string | null; head?: string | null; pull_number?: number | null },
  ) =>
    request<FetchDiffResult>(
      '/api/settings/repository/fetch-diff',
      { method: 'POST', body: JSON.stringify(data) },
      token,
    ),

  getRepositoryPullRequests: (token: string) =>
    request<{ pull_requests: GitHubPullRequest[] }>(
      '/api/settings/repository/pull-requests',
      {},
      token,
    ),

  getJiraStatus: (token: string) =>
    request<JiraConnectionStatus>('/api/settings/jira/status', {}, token),

  startJiraConnection: (token: string) =>
    request<{ authorization_url: string }>(
      '/api/settings/jira/connect',
      { method: 'POST' },
      token,
    ),

  disconnectJira: (token: string) =>
    request<void>('/api/settings/jira', { method: 'DELETE' }, token),

  getAssignedJiraIssues: (
    token: string,
    nextPageToken?: string | null,
    projectKey?: string | null,
  ) => {
    const query = new URLSearchParams()
    if (nextPageToken) query.set('next_page_token', nextPageToken)
    if (projectKey) query.set('project_key', projectKey)
    const queryString = query.toString()
    return request<JiraIssuePage>(
      `/api/settings/jira/issues${queryString ? `?${queryString}` : ''}`,
      {},
      token,
    )
  },

  getJiraIssue: (token: string, issueKey: string) =>
    request<JiraIssue>(
      `/api/settings/jira/issues/${encodeURIComponent(issueKey)}`,
      {},
      token,
    ),

  getJiraProjects: (token: string) =>
    request<{ projects: JiraProject[] }>('/api/settings/jira/projects', {}, token),

  createJiraIssue: (
    token: string,
    data: { project_key: string; summary: string; description: string },
  ) =>
    request<JiraCreatedIssue>(
      '/api/settings/jira/issues',
      { method: 'POST', body: JSON.stringify(data) },
      token,
    ),
}

export { ApiError }
