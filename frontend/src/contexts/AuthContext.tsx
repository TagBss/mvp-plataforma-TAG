import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { api } from '../services/api'

// Tipos
interface User {
  id: number
  email: string
  username: string
  roles: string[]
  permissions: string[]
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface LoginCredentials {
  email: string
  password: string
}

interface AuthContextType {
  state: AuthState
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  hasPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}

// Actions
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'LOAD_USER_START' }
  | { type: 'LOAD_USER_SUCCESS'; payload: User }
  | { type: 'LOAD_USER_FAILURE' }

// Initial State
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: false,
  error: null
}

// Reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null
      }
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null
      }
    
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload
      }
    
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      }
    
    case 'LOAD_USER_START':
      return {
        ...state,
        isLoading: true
      }
    
    case 'LOAD_USER_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false
      }
    
    case 'LOAD_USER_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false
      }
    
    default:
      return state
  }
}

// Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Provider Component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Configurar interceptor do axios para incluir token
  useEffect(() => {
    if (state.token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${state.token}`
      localStorage.setItem('token', state.token)
    } else {
      delete api.defaults.headers.common['Authorization']
      localStorage.removeItem('token')
    }
  }, [state.token])

  // Carregar usuário se token existir
  useEffect(() => {
    const loadUser = async () => {
      if (state.token && !state.user) {
        try {
          dispatch({ type: 'LOAD_USER_START' })
          const response = await api.get('/auth/me')
          dispatch({ type: 'LOAD_USER_SUCCESS', payload: response.data })
        } catch (error) {
          dispatch({ type: 'LOAD_USER_FAILURE' })
        }
      }
    }

    loadUser()
  }, [state.token, state.user])

  // Login function
  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: 'LOGIN_START' })
      
      const response = await api.post('/auth/login', credentials)
      const { user, token } = response.data
      
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, token } })
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Erro ao fazer login'
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage })
      throw new Error(errorMessage)
    }
  }

  // Logout function
  const logout = () => {
    dispatch({ type: 'LOGOUT' })
  }

  // Permission check
  const hasPermission = (permission: string): boolean => {
    if (!state.user) return false
    return state.user.permissions.includes(permission) || 
           state.user.roles.includes('admin')
  }

  // Role check
  const hasRole = (role: string): boolean => {
    if (!state.user) return false
    return state.user.roles.includes(role)
  }

  const value: AuthContextType = {
    state,
    login,
    logout,
    hasPermission,
    hasRole
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook para usar o contexto
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
} 