import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { FileText, Download, Filter } from 'lucide-react'
import { useHealthCheck } from '../hooks/useFinancialData'
import DreTable from '../components/table-dre'
import LoadingSpinner from '../components/LoadingSpinner'

const DrePage = () => {
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
            <FileText className="h-8 w-8" />
            Demonstração do Resultado do Exercício (DRE)
          </h1>
          <p className="text-muted-foreground">
            Análise detalhada das receitas, custos e despesas da empresa
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
          <CardTitle>Relatório DRE</CardTitle>
          <CardDescription>
            Demonstrativo detalhado dos resultados financeiros
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DreTable />
        </CardContent>
      </Card>
    </div>
  )
}

export default DrePage
