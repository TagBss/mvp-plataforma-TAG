import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { api, apiLongTimeout } from '../services/api'
import LoadingSpinner from './LoadingSpinner'

type TestStatus = 'idle' | 'loading' | 'success' | 'error'

export default function TimeoutTest() {
  const [testStatus, setTestStatus] = useState('idle' as 'idle' | 'loading' | 'success' | 'error')
  const [testTime, setTestTime] = useState<number>(0)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [useLongTimeout, setUseLongTimeout] = useState<boolean>(false)

  const runTest = async () => {
    setTestStatus('loading')
    setTestTime(0)
    setErrorMessage('')
    
    const startTime = Date.now()
    const interval = setInterval(() => {
      setTestTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    try {
      const apiInstance = useLongTimeout ? apiLongTimeout : api
      console.log(`🔄 Iniciando teste com ${useLongTimeout ? 'timeout longo' : 'timeout normal'}...`)
      
      const response = await apiInstance.get('/dre')
      console.log('✅ Teste concluído:', response.data)
      
      setTestStatus('success')
    } catch (error: any) {
      console.error('❌ Erro no teste:', error)
      setErrorMessage(error.message || 'Erro desconhecido')
      setTestStatus('error')
    } finally {
      clearInterval(interval)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success'
      case 'error':
        return 'destructive'
      case 'loading':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'idle':
        return 'Pronto'
      case 'loading':
        return 'Testando...'
      case 'success':
        return 'Sucesso'
      case 'error':
        return 'Erro'
      default:
        return 'Desconhecido'
    }
  }

  if (testStatus === 'loading') {
    return (
      <LoadingSpinner 
        title={`Testando Timeout (${useLongTimeout ? '5 min' : '2 min'})`}
        description={`Tempo decorrido: ${testTime}s`}
        showProgress={true}
        progress={Math.min((testTime / 60) * 100, 95)} // Simulação de progresso
      />
    )
  }

  return (
    <div className="p-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Teste de Timeout</CardTitle>
          <CardDescription>
            Testando se o timeout foi resolvido com diferentes configurações
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-sm font-medium mb-2">Status do Teste</div>
              <Badge variant={getStatusColor(testStatus)}>
                {getStatusText(testStatus)}
              </Badge>
            </div>
            
            <div className="text-center">
              <div className="text-sm font-medium mb-2">Tempo Decorrido</div>
              <div className="text-lg font-bold">{testTime}s</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="useLongTimeout"
                checked={useLongTimeout}
                onChange={(e) => setUseLongTimeout(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="useLongTimeout" className="text-sm">
                Usar timeout longo (5 minutos)
              </label>
            </div>
            
            <div className="text-xs text-muted-foreground">
              {useLongTimeout ? 
                'Timeout: 5 minutos - Para operações muito pesadas' :
                'Timeout: 2 minutos - Para operações normais'
              }
            </div>
          </div>

          <div className="flex space-x-2">
            <Button 
              onClick={runTest} 
              disabled={testStatus === ('loading' as any)}
              className="flex-1"
            >
              {testStatus === ('loading' as any) ? 'Testando...' : 'Executar Teste'}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={() => {
                setTestStatus('idle')
                setTestTime(0)
                setErrorMessage('')
              }}
            >
              Reset
            </Button>
          </div>

          {errorMessage && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-md">
              <div className="text-red-800 dark:text-red-200">
                <strong>Erro:</strong> {errorMessage}
              </div>
            </div>
          )}

          <div className="text-xs text-muted-foreground space-y-1">
            <p>💡 Dica: Se o teste falhar com timeout, tente com timeout longo</p>
            <p>⏱️ O backend pode demorar para processar o Excel na primeira vez</p>
            <p>🔄 Próximas execuções serão mais rápidas</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 