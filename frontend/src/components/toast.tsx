"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title?: string
  message: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  success: (message: string, title?: string) => void
  error: (message: string, title?: string) => void
  warning: (message: string, title?: string) => void
  info: (message: string, title?: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

// Toast Provider
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast = { ...toast, id }
    
    setToasts((prev) => [...prev, newToast])

    // Auto remove after duration
    const duration = toast.duration || 5000
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  // Convenience methods
  const success = (message: string, title?: string) => {
    addToast({ type: 'success', message, title })
  }

  const error = (message: string, title?: string) => {
    addToast({ type: 'error', message, title, duration: 7000 })
  }

  const warning = (message: string, title?: string) => {
    addToast({ type: 'warning', message, title, duration: 6000 })
  }

  const info = (message: string, title?: string) => {
    addToast({ type: 'info', message, title })
  }

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        success,
        error,
        warning,
        info,
      }}
    >
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

// Hook para usar o toast
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Container dos toasts
function ToastContainer() {
  const { toasts } = useToast()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}

// Item individual do toast
function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToast()
  const [isExiting, setIsExiting] = useState(false)

  const handleRemove = () => {
    setIsExiting(true)
    setTimeout(() => {
      removeToast(toast.id)
    }, 300) // Match animation duration
  }

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />
      default:
        return null
    }
  }

  const getToastStyles = () => {
    const baseStyles = "p-4 rounded-lg border shadow-lg backdrop-blur-sm transition-all duration-300 transform"
    
    if (isExiting) {
      return `${baseStyles} translate-x-full opacity-0`
    }

    switch (toast.type) {
      case 'success':
        return `${baseStyles} bg-green-50 border-green-200 dark:bg-green-950/50 dark:border-green-800`
      case 'error':
        return `${baseStyles} bg-red-50 border-red-200 dark:bg-red-950/50 dark:border-red-800`
      case 'warning':
        return `${baseStyles} bg-yellow-50 border-yellow-200 dark:bg-yellow-950/50 dark:border-yellow-800`
      case 'info':
        return `${baseStyles} bg-blue-50 border-blue-200 dark:bg-blue-950/50 dark:border-blue-800`
      default:
        return `${baseStyles} bg-background border-border`
    }
  }

  return (
    <div className={getToastStyles()}>
      <div className="flex items-start gap-3">
        {getIcon()}
        <div className="flex-1 min-w-0">
          {toast.title && (
            <p className="font-medium text-sm text-foreground mb-1">
              {toast.title}
            </p>
          )}
          <p className="text-sm text-muted-foreground leading-relaxed">
            {toast.message}
          </p>
          {toast.action && (
            <button
              onClick={() => {
                toast.action!.onClick()
                handleRemove()
              }}
              className="mt-2 text-sm font-medium text-primary hover:text-primary/80 underline"
            >
              {toast.action.label}
            </button>
          )}
        </div>
        <button
          onClick={handleRemove}
          className="text-muted-foreground hover:text-foreground transition-colors p-1 -m-1"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

// Toast helpers para casos específicos
export const toastHelpers = {
  // Financial data toasts
  dataLoaded: (count: number) => ({
    type: 'success' as const,
    message: `${count} registros carregados com sucesso`,
    title: 'Dados Atualizados'
  }),

  dataError: (error: string) => ({
    type: 'error' as const,
    message: `Erro ao carregar dados: ${error}`,
    title: 'Erro de Conexão'
  }),

  filtersApplied: (count: number) => ({
    type: 'info' as const,
    message: `${count} registros encontrados`,
    title: 'Filtros Aplicados'
  }),

  exportSuccess: (type: string) => ({
    type: 'success' as const,
    message: `Relatório ${type} exportado com sucesso`,
    title: 'Export Concluído'
  }),

  // Authentication toasts
  loginSuccess: (userName: string) => ({
    type: 'success' as const,
    message: `Bem-vindo de volta, ${userName}!`,
    title: 'Login Realizado'
  }),

  logoutSuccess: () => ({
    type: 'info' as const,
    message: 'Você foi desconectado com segurança',
    title: 'Logout Realizado'
  }),

  sessionExpired: () => ({
    type: 'warning' as const,
    message: 'Sua sessão expirou. Faça login novamente.',
    title: 'Sessão Expirada',
    duration: 8000
  }),

  // Cache toasts
  cacheCleared: () => ({
    type: 'info' as const,
    message: 'Cache limpo. Dados serão recarregados.',
    title: 'Cache Atualizado'
  }),

  // Performance toasts
  slowConnection: () => ({
    type: 'warning' as const,
    message: 'Conexão lenta detectada. Alguns recursos podem demorar para carregar.',
    title: 'Conexão Lenta'
  })
}

// Hook for specific toast scenarios
export function useFinancialToast() {
  const toast = useToast()

  return {
    dataLoaded: (count: number) => toast.addToast(toastHelpers.dataLoaded(count)),
    dataError: (error: string) => toast.addToast(toastHelpers.dataError(error)),
    filtersApplied: (count: number) => toast.addToast(toastHelpers.filtersApplied(count)),
    exportSuccess: (type: string) => toast.addToast(toastHelpers.exportSuccess(type)),
    cacheCleared: () => toast.addToast(toastHelpers.cacheCleared()),
    slowConnection: () => toast.addToast(toastHelpers.slowConnection()),
  }
}
