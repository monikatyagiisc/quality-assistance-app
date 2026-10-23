import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, type User } from '../api/client'
import { AuthContext } from './authContext'

const TOKEN_KEY = 'qa_access_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)))

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
