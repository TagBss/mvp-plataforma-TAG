import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Alert, AlertDescription } from './ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { api } from '../services/api'

export default function DebugPanel() {
  const [tests, setTests] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  const runTest = async (testName: string, testFn: () => Promise<any>) => {
    setLoading(true)
    try {
      const result = await testFn()
      setTests(prev => ({
        ...prev,
        [testName]: { status: 'success', data: result, timestamp: new Date().toISOString() }
      }))
    } catch (error: any) {
      setTests(prev => ({
        ...prev,
        [testName]: { 
          status: 'error', 
          error: error.message || 'Erro desconhecido',
          timestamp: new Date().toISOString()
        }
      }))
    } finally {
      setLoading(false)
    }
  }

  const testHealth = () => runTest('health', () => api.get('/health'))
  const testDre = () => runTest('dre', () => api.get('/dre'))
  const testDfc = () => runTest('dfc', () => api.get('/dfc'))
  const testRoot = () => runTest('root', () => api.get('/'))

  const runAllTests = async () => {
    await Promise.all([
      testHealth(),
      testDre(),
      testDfc(),
      testRoot()
    ])
  }

  useEffect(() => {
    runAllTests()
  }, [])

  const getStatusColor = (status: string) => {
    return status === 'success' ? 'text-green-600' : 'text-red-600'
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Painel de Debug - Backend</CardTitle>
        <CardDescription>
          Testes de conectividade e endpoints da API
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex space-x-2">
            <Button onClick={runAllTests} disabled={loading}>
              {loading ? 'Testando...' : 'Executar Todos os Testes'}
            </Button>
            <Button variant="outline" onClick={testHealth} disabled={loading}>
              Testar Health
            </Button>
            <Button variant="outline" onClick={testDre} disabled={loading}>
              Testar DRE
            </Button>
            <Button variant="outline" onClick={testDfc} disabled={loading}>
              Testar DFC
            </Button>
          </div>

          <Tabs defaultValue="results" className="w-full">
            <TabsList>
              <TabsTrigger value="results">Resultados</TabsTrigger>
              <TabsTrigger value="network">Network</TabsTrigger>
              <TabsTrigger value="console">Console</TabsTrigger>
            </TabsList>

            <TabsContent value="results" className="space-y-4">
              {Object.entries(tests).map(([testName, test]) => (
                <Card key={testName}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg capitalize">{testName}</CardTitle>
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          test.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                        <span className={`text-sm ${getStatusColor(test.status)}`}>
                          {test.status === 'success' ? '✅ Sucesso' : '❌ Erro'}
                        </span>
                      </div>
                    </div>
                    <CardDescription>
                      {test.timestamp && new Date(test.timestamp).toLocaleTimeString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {test.status === 'error' ? (
                      <Alert>
                        <AlertDescription>
                          <strong>Erro:</strong> {test.error}
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded-md">
                        <pre className="text-xs overflow-auto">
                          {JSON.stringify(test.data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="network">
              <Card>
                <CardHeader>
                  <CardTitle>Informações de Rede</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div><strong>Base URL:</strong> http://127.0.0.1:8000</div>
                    <div><strong>Timeout:</strong> 30 segundos</div>
                    <div><strong>CORS:</strong> Configurado no backend</div>
                    <div><strong>Content-Type:</strong> application/json</div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="console">
              <Card>
                <CardHeader>
                  <CardTitle>Console Logs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-black text-green-400 p-4 rounded-md h-64 overflow-auto">
                    <div className="text-xs">
                      <div>🔍 Abra o DevTools (F12) para ver logs detalhados</div>
                      <div>📡 Verifique a aba Network para requisições</div>
                      <div>🐛 Verifique a aba Console para erros</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </CardContent>
    </Card>
  )
} 