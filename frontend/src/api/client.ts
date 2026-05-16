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

export type AssistanceResult = {
  id: string
  session_id: string
  response: string
  status: string
  created_at: string
}

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

const REQUEST_TIMEOUT_MS = 15_000

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        0,
        'Request timed out. Is the backend running on ' + API_URL + '?',
        'timeout',
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

  me: (token: string) => request<User>('/api/auth/me', {}, token),

  assist: (
    token: string,
    data: {
      requirements: string
      user_stories?: string | null
      code_diffs?: string | null
      session_id?: string | null
    },
  ) =>
    request<AssistanceResult>('/api/assist', { method: 'POST', body: JSON.stringify(data) }, token),

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
}

export { ApiError }
