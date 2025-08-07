import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { api } from '../services/api'

export default function SimpleTest() {
  const [healthStatus, setHealthStatus] = useState<'loading' | 'healthy' | 'error'>('loading')
  const [dreStatus, setDreStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [dfcStatus, setDfcStatus] = useState<'loading' | 'success' | 'error'>('loading')

  const testHealth = async () => {
    try {
      setHealthStatus('loading')
      const response = await api.get('/health')
      console.log('Health response:', response.data)
      setHealthStatus('healthy')
    } catch (error) {
      console.error('Health error:', error)
      setHealthStatus('error')
    }
  }

  const testDre = async () => {
    try {
      setDreStatus('loading')
      const response = await api.get('/dre')
      console.log('DRE response:', response.data)
      setDreStatus('success')
    } catch (error) {
      console.error('DRE error:', error)
      setDreStatus('error')
    }
  }

  const testDfc = async () => {
    try {
      setDfcStatus('loading')
      const response = await api.get('/dfc')
      console.log('DFC response:', response.data)
      setDfcStatus('success')
    } catch (error) {
      console.error('DFC error:', error)
      setDfcStatus('error')
    }
  }

  useEffect(() => {
    testHealth()
    testDre()
    testDfc()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'success':
        return 'success'
      case 'error':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'loading':
        return 'Testando...'
      case 'healthy':
      case 'success':
        return 'OK'
      case 'error':
        return 'Erro'
      default:
        return 'Desconhecido'
    }
  }

  return (
    <div className="p-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Teste Simples - Backend</CardTitle>
          <CardDescription>
            Verificando se os endpoints estão funcionando
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-sm font-medium mb-2">Health Check</div>
              <Badge variant={getStatusColor(healthStatus)}>
                {getStatusText(healthStatus)}
              </Badge>
            </div>
            
            <div className="text-center">
              <div className="text-sm font-medium mb-2">DRE</div>
              <Badge variant={getStatusColor(dreStatus)}>
                {getStatusText(dreStatus)}
              </Badge>
            </div>
            
            <div className="text-center">
              <div className="text-sm font-medium mb-2">DFC</div>
              <Badge variant={getStatusColor(dfcStatus)}>
                {getStatusText(dfcStatus)}
              </Badge>
            </div>
          </div>

          <div className="flex space-x-2">
            <Button onClick={testHealth} variant="outline" size="sm">
              Testar Health
            </Button>
            <Button onClick={testDre} variant="outline" size="sm">
              Testar DRE
            </Button>
            <Button onClick={testDfc} variant="outline" size="sm">
              Testar DFC
            </Button>
          </div>

          <div className="text-xs text-muted-foreground">
            <p>✅ Se todos os testes passarem, o Dashboard deve funcionar</p>
            <p>🔍 Verifique o console (F12) para logs detalhados</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 