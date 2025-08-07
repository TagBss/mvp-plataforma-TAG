"use client"

import React from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    })

    // Log error to monitoring service (Sentry, etc.)
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    // TODO: Integrar com serviço de monitoramento
    // Sentry.captureException(error, { extra: errorInfo })
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render() {
    if (this.state.hasError) {
      // Render custom fallback UI
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return (
          <FallbackComponent
            error={this.state.error!}
            resetError={this.resetError}
          />
        )
      }

      // Default fallback UI
      return <DefaultErrorFallback error={this.state.error!} resetError={this.resetError} />
    }

    return this.props.children
  }
}

// Default Error Fallback Component
function DefaultErrorFallback({ 
  error, 
  resetError 
}: { 
  error: Error
  resetError: () => void 
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 text-destructive">
            <AlertTriangle className="h-full w-full" />
          </div>
          <CardTitle className="text-xl">Oops! Algo deu errado</CardTitle>
          <CardDescription>
            Ocorreu um erro inesperado. Nossa equipe foi notificada e já está trabalhando na correção.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
            <strong>Erro:</strong> {error.message}
          </div>
          
          <div className="flex gap-2">
            <Button onClick={resetError} className="flex-1">
              <RefreshCw className="mr-2 h-4 w-4" />
              Tentar Novamente
            </Button>
            <Button 
              variant="outline" 
              onClick={() => window.location.href = '/'}
              className="flex-1"
            >
              <Home className="mr-2 h-4 w-4" />
              Início
            </Button>
          </div>
          
          <details className="text-xs text-muted-foreground">
            <summary className="cursor-pointer hover:text-foreground">
              Detalhes técnicos (para desenvolvedores)
            </summary>
            <pre className="mt-2 whitespace-pre-wrap bg-muted p-2 rounded text-xs overflow-auto">
              {error.stack}
            </pre>
          </details>
        </CardContent>
      </Card>
    </div>
  )
}

// Hook para resetar error boundary programaticamente
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const captureError = React.useCallback((error: Error) => {
    setError(error)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { captureError, resetError }
}

// Specific Error Fallbacks
export function FinancialDataErrorFallback({ 
  error, 
  resetError 
}: { 
  error: Error
  resetError: () => void 
}) {
  return (
    <Card className="border-destructive">
      <CardHeader>
        <CardTitle className="text-destructive flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Erro nos Dados Financeiros
        </CardTitle>
        <CardDescription>
          Não foi possível carregar os dados financeiros. Verifique sua conexão e tente novamente.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={resetError} className="w-full">
          <RefreshCw className="mr-2 h-4 w-4" />
          Recarregar Dados
        </Button>
      </CardContent>
    </Card>
  )
}

export function ChartErrorFallback({ 
  error, 
  resetError 
}: { 
  error: Error
  resetError: () => void 
}) {
  return (
    <Card className="border-destructive">
      <CardContent className="p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-destructive mb-2" />
        <p className="text-sm text-muted-foreground mb-4">
          Erro ao renderizar o gráfico
        </p>
        <Button size="sm" onClick={resetError}>
          Tentar Novamente
        </Button>
      </CardContent>
    </Card>
  )
}
