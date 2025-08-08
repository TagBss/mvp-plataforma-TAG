import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { TrendingUp, Download, Filter, Activity } from 'lucide-react'
import { useHealthCheck } from '../hooks/useFinancialData'
import DfcTable from '../components/table-dfc/index-postgresql'
import LoadingSpinner from '../components/LoadingSpinner'

const DfcPage = () => {
  const { health, loading, error } = useHealthCheck()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Erro ao conectar com o servidor: {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8" />
            Demonstração dos Fluxos de Caixa (DFC)
          </h1>
          <p className="text-muted-foreground">
            Análise dos fluxos de caixa operacionais, de investimento e de financiamento
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filtros
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      <Separator />

      <Card>
        <CardHeader>
          <CardTitle>Relatório DFC</CardTitle>
          <CardDescription>
            Demonstrativo dos fluxos de caixa por categoria
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DfcTable />
        </CardContent>
      </Card>
    </div>
  )
}

export default DfcPage
