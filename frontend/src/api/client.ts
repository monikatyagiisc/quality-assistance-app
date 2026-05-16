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

export type AssistanceResult = {
  id: string
  session_id: string
  response: string
  status: string
  created_at: string
}

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

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

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : 'Request failed'
    throw new ApiError(response.status, detail)
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
}

export { ApiError }
