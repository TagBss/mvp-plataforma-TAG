import React, { useState } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { ErrorBoundary, FinancialDataErrorFallback } from './error-boundary'
import { KPIsSkeleton, ChartSkeleton, DashboardSkeleton } from './loading-skeletons'
import { useToast, useFinancialToast } from './toast'

// Wrapper para componentes financeiros com error handling
export function FinancialComponentWrapper({ 
  children,
  isLoading = false,
  hasError = false,
  onRetry
}: {
  children: React.ReactNode
  isLoading?: boolean
  hasError?: boolean
  onRetry?: () => void
}) {
  if (isLoading) {
    return <KPIsSkeleton />
  }

  if (hasError) {
    return (
      <ErrorBoundary fallback={FinancialDataErrorFallback}>
        {children}
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary fallback={FinancialDataErrorFallback}>
      {children}
    </ErrorBoundary>
  )
}

// Hook para gerenciar estados de carregamento dos dados financeiros
export function useFinancialDataState() {
  const [isLoading, setIsLoading] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const financialToast = useFinancialToast()

  const startLoading = () => {
    setIsLoading(true)
    setHasError(false)
    setError(null)
  }

  const stopLoading = () => {
    setIsLoading(false)
  }

  const handleError = (error: Error | string) => {
    const errorObj = typeof error === 'string' ? new Error(error) : error
    setError(errorObj)
    setHasError(true)
    setIsLoading(false)
    financialToast.dataError(errorObj.message)
  }

  const handleSuccess = (message?: string, count?: number) => {
    setHasError(false)
    setError(null)
    setIsLoading(false)
    
    if (message) {
      financialToast.dataLoaded(count || 0)
    }
  }

  const retry = () => {
    setHasError(false)
    setError(null)
  }

  return {
    isLoading,
    hasError,
    error,
    startLoading,
    stopLoading,
    handleError,
    handleSuccess,
    retry
  }
}

// Exemplo de uso melhorado no componente KPI
export function KPICardWithErrorHandling({
  title,
  value,
  description,
  icon: Icon,
  trend,
  isLoading = false,
  error
}: {
  title: string
  value: string | number
  description?: string
  icon?: any
  trend?: 'up' | 'down' | 'neutral'
  isLoading?: boolean
  error?: Error | null
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="h-4 w-[100px] bg-muted animate-pulse rounded" />
          <div className="h-4 w-4 bg-muted animate-pulse rounded" />
        </CardHeader>
        <CardContent>
          <div className="h-8 w-[120px] bg-muted animate-pulse rounded mb-1" />
          <div className="h-3 w-[80px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="p-6 text-center">
          <p className="text-sm text-destructive">Erro ao carregar {title}</p>
        </CardContent>
      </Card>
    )
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      default:
        return Icon ? <Icon className="h-4 w-4" /> : null
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {getTrendIcon()}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}
