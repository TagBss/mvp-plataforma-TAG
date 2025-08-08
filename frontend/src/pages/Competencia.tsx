import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'
import { useDashboard, useHealthCheck } from '../hooks/useFinancialData'
import LoadingSpinner from '../components/LoadingSpinner'
import DashCompetencia from '../components/kpis-competencia/index-postgresql'

const Competencia = () => {
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
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Dashboard de Competência</h1>
        <p className="text-muted-foreground">
          Análise de performance por período de competência
        </p>
      </div>

      <Separator />

      <DashCompetencia />
    </div>
  )
}

export default Competencia
