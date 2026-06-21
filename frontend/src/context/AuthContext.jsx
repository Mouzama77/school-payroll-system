import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getMe } from '../api/auth'
import { TOKEN_KEY, USER_KEY } from '../api/axios'
import { decodeToken, isTokenExpired } from '../utils/auth'

const AuthContext = createContext(null)

function readStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(() => readStoredUser())

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const persistSession = useCallback((accessToken, profile) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(profile))
    setToken(accessToken)
    setUser(profile)
  }, [])

  const login = useCallback(
    async (loginResponse) => {
      const payload = decodeToken(loginResponse.access_token)
      const profile = {
        email: payload?.email,
        role: loginResponse.role,
        must_change_password: loginResponse.must_change_password,
        employee_id: null,
      }
      persistSession(loginResponse.access_token, profile)
      try {
        const me = await getMe()
        const enriched = {
          email: me.email,
          role: me.role,
          must_change_password: me.must_change_password,
          employee_id: me.employee_id,
        }
        persistSession(loginResponse.access_token, enriched)
      } catch {
        // keep basic profile from token
      }
    },
    [persistSession],
  )

  const refreshProfile = useCallback(async () => {
    if (!token) return
    const me = await getMe()
    const profile = {
      email: me.email,
      role: me.role,
      must_change_password: me.must_change_password,
      employee_id: me.employee_id,
    }
    localStorage.setItem(USER_KEY, JSON.stringify(profile))
    setUser(profile)
  }, [token])

  useEffect(() => {
    if (!token) return undefined

    if (isTokenExpired(token)) {
      logout()
      return undefined
    }

    const payload = decodeToken(token)
    if (!payload?.exp) return undefined

    const timeout = payload.exp * 1000 - Date.now()
    const timer = setTimeout(() => logout(), timeout)
    return () => clearTimeout(timer)
  }, [token, logout])

  const value = useMemo(
    () => ({
      token,
      user,
      role: user?.role,
      isAuthenticated: Boolean(token && user && !isTokenExpired(token)),
      mustChangePassword: user?.must_change_password,
      login,
      logout,
      refreshProfile,
    }),
    [token, user, login, logout, refreshProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
