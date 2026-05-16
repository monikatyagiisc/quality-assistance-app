import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, ApiError, type User } from '../api/client'

const TOKEN_KEY = 'qa_access_token'

type AuthContextValue = {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (fullName: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(true)

  const persistAuth = useCallback((accessToken: string, nextUser: User) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    setToken(accessToken)
    setUser(nextUser)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }

    api
      .me(token)
      .then(setUser)
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, [token, logout])

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await api.login({ email, password })
      persistAuth(result.access_token, result.user)
    },
    [persistAuth],
  )

  const register = useCallback(
    async (fullName: string, email: string, password: string) => {
      const result = await api.register({ full_name: fullName, email, password })
      persistAuth(result.access_token, result.user)
    },
    [persistAuth],
  )

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}

export { ApiError }
