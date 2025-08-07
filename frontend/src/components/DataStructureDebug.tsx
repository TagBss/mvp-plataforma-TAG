import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { api } from '../services/api'

export default function DataStructureDebug() {
  const [dreData, setDreData] = useState<any>(null)
  const [dfcData, setDfcData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const fetchData = async () => {
    setLoading(true)
    setError('')
    
    try {
      // Buscar dados DRE
      console.log('🔍 Buscando dados DRE...')
      const dreResponse = await api.get('/dre')
      console.log('✅ DRE Response:', dreResponse.data)
      setDreData(dreResponse.data)
      
      // Buscar dados DFC
      console.log('🔍 Buscando dados DFC...')
      const dfcResponse = await api.get('/dfc')
      console.log('✅ DFC Response:', dfcResponse.data)
      setDfcData(dfcResponse.data)
      
    } catch (err: any) {
      console.error('❌ Erro ao buscar dados:', err)
      setError(err.message || 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const renderDataStructure = (data: any, title: string) => {
    if (!data) return <div className="text-muted-foreground">Nenhum dado disponível</div>
    
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Estrutura Geral</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs space-y-1">
                <div><strong>Keys disponíveis:</strong></div>
                <ul className="list-disc list-inside space-y-1">
                  {Object.keys(data).map(key => (
                    <li key={key} className="text-blue-600">{key}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">total_geral_real</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs">
                {data.total_geral_real ? (
                  <div>
                    <div><strong>Keys:</strong></div>
                    <ul className="list-disc list-inside space-y-1">
                      {Object.keys(data.total_geral_real).map(key => (
                        <li key={key} className="text-green-600">
                          {key}: {data.total_geral_real[key]}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="text-red-600">❌ total_geral_real é undefined</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Dados Completos (JSON)</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-auto max-h-96">
              {JSON.stringify(data, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <Card className="w-full max-w-6xl mx-auto">
      <CardHeader>
        <CardTitle>Debug - Estrutura de Dados</CardTitle>
        <CardDescription>
          Analisando a estrutura dos dados vindos do backend
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex space-x-2">
            <Button onClick={fetchData} disabled={loading}>
              {loading ? 'Buscando...' : 'Atualizar Dados'}
            </Button>
          </div>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-md">
              <div className="text-red-800 dark:text-red-200">
                <strong>Erro:</strong> {error}
              </div>
            </div>
          )}

          <Tabs defaultValue="dre" className="w-full">
            <TabsList>
              <TabsTrigger value="dre">DRE</TabsTrigger>
              <TabsTrigger value="dfc">DFC</TabsTrigger>
            </TabsList>

            <TabsContent value="dre">
              <Card>
                <CardHeader>
                  <CardTitle>Estrutura dos Dados DRE</CardTitle>
                </CardHeader>
                <CardContent>
                  {renderDataStructure(dreData, 'DRE')}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="dfc">
              <Card>
                <CardHeader>
                  <CardTitle>Estrutura dos Dados DFC</CardTitle>
                </CardHeader>
                <CardContent>
                  {renderDataStructure(dfcData, 'DFC')}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </CardContent>
    </Card>
  )
} 