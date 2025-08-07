import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'

interface LoadingSpinnerProps {
  title?: string
  description?: string
  showProgress?: boolean
  progress?: number
}

export default function LoadingSpinner({ 
  title = "Carregando dados...", 
  description = "Isso pode demorar alguns minutos na primeira vez",
  showProgress = false,
  progress = 0
}: LoadingSpinnerProps) {
  return (
    <div className="p-8">
      <Card className="max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <div className="flex flex-col items-center space-y-4">
            {/* Spinner animado */}
            <div className="relative">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 bg-blue-600 rounded-full animate-pulse"></div>
              </div>
            </div>

            {/* Barra de progresso */}
            {showProgress && (
              <div className="w-full max-w-xs">
                <div className="flex justify-between text-sm text-muted-foreground mb-2">
                  <span>Progresso</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Dicas */}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>💡 Dica: O backend está processando um arquivo Excel grande</p>
              <p>⏱️ Primeira execução pode demorar até 2-3 minutos</p>
              <p>🔄 Próximas execuções serão mais rápidas</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 