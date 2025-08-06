import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Alert, AlertDescription } from './ui/alert'
import { api } from '../services/api'

export default function TestConnection() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const testConnection = async () => {
    setStatus('loading')
    setError('')
    
    try {
      // Teste 1: Health check
      console.log('🔍 Testando health check...')
      const healthResponse = await api.get('/health')
      console.log('✅ Health check:', healthResponse.data)
      
      // Teste 2: DRE endpoint
      console.log('🔍 Testando endpoint DRE...')
      const dreResponse = await api.get('/dre')
      console.log('✅ DRE response:', dreResponse.data)
      
      setData({
        health: healthResponse.data,
        dre: dreResponse.data
      })
      setStatus('success')
    } catch (err: any) {
      console.error('❌ Erro no teste:', err)
      setError(err.message || 'Erro desconhecido')
      setStatus('error')
    }
  }

  useEffect(() => {
    testConnection()
  }, [])

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Teste de Conexão com Backend</CardTitle>
        <CardDescription>
          Verificando se o frontend consegue se comunicar com a API
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            status === 'loading' ? 'bg-yellow-500 animate-pulse' :
            status === 'success' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-sm">
            {status === 'loading' && 'Testando conexão...'}
            {status === 'success' && 'Conexão bem-sucedida!'}
            {status === 'error' && 'Erro na conexão'}
          </span>
        </div>

        {status === 'error' && (
          <Alert>
            <AlertDescription>
              <strong>Erro:</strong> {error}
              <br />
              <strong>Verifique:</strong>
              <ul className="list-disc list-inside mt-2">
                <li>Se o backend está rodando em http://127.0.0.1:8000</li>
                <li>Se não há bloqueio de CORS</li>
                <li>Se os endpoints /health e /dre existem</li>
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {status === 'success' && data && (
          <div className="space-y-2">
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
              <h4 className="font-medium text-green-800 dark:text-green-200">Health Check:</h4>
              <pre className="text-xs mt-1 text-green-700 dark:text-green-300">
                {JSON.stringify(data.health, null, 2)}
              </pre>
            </div>
            
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
              <h4 className="font-medium text-blue-800 dark:text-blue-200">DRE Data:</h4>
              <pre className="text-xs mt-1 text-blue-700 dark:text-blue-300">
                {JSON.stringify(data.dre, null, 2)}
              </pre>
            </div>
          </div>
        )}

        <Button onClick={testConnection} disabled={status === 'loading'}>
          Testar Novamente
        </Button>
      </CardContent>
    </Card>
  )
} 