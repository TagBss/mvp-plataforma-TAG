import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Skeleton } from './ui/skeleton'
import { Card, CardContent } from './ui/card'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
  requiredRole?: string
  fallback?: React.ReactNode
}

export function ProtectedRoute({ 
  children, 
  requiredPermission, 
  requiredRole,
  fallback 
}: ProtectedRouteProps) {
  const { state, hasPermission, hasRole } = useAuth()
  const location = useLocation()

  // Se está carregando, mostrar skeleton
  if (state.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardContent className="p-6">
            <div className="space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Se não está autenticado, redirecionar para login
  if (!state.isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Se precisa de permissão específica
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <Card className="w-full max-w-md">
            <CardContent className="p-6 text-center">
              <h2 className="text-xl font-semibold text-destructive mb-2">
                Acesso Negado
              </h2>
              <p className="text-muted-foreground">
                Você não tem permissão para acessar esta página.
              </p>
            </CardContent>
          </Card>
        </div>
      )
    )
  }

  // Se precisa de role específica
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <Card className="w-full max-w-md">
            <CardContent className="p-6 text-center">
              <h2 className="text-xl font-semibold text-destructive mb-2">
                Acesso Negado
              </h2>
              <p className="text-muted-foreground">
                Você não tem o nível de acesso necessário para esta página.
              </p>
            </CardContent>
          </Card>
        </div>
      )
    )
  }

  // Se passou por todas as verificações, renderizar children
  return <>{children}</>
}

// Hook para verificar se usuário tem permissão
export function usePermission(permission: string) {
  const { hasPermission } = useAuth()
  return hasPermission(permission)
}

// Hook para verificar se usuário tem role
export function useRole(role: string) {
  const { hasRole } = useAuth()
  return hasRole(role)
}

// Componente para mostrar/esconder baseado em permissão
export function PermissionGate({ 
  permission, 
  children, 
  fallback = null 
}: { 
  permission: string
  children: React.ReactNode
  fallback?: React.ReactNode
}) {
  const hasPermission = usePermission(permission)
  
  if (!hasPermission) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
}

// Componente para mostrar/esconder baseado em role
export function RoleGate({ 
  role, 
  children, 
  fallback = null 
}: { 
  role: string
  children: React.ReactNode
  fallback?: React.ReactNode
}) {
  const hasRole = useRole(role)
  
  if (!hasRole) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
} 