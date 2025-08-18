import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Separator } from '../components/ui/separator'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'
import { useDashboard, useHealthCheck } from '../hooks/useFinancialData'
import DreTable from '../components/table-dre-postgresql'
import DfcTable from '../components/table-dfc'
import LoadingSpinner from '../components/LoadingSpinner'

// Função para formatar valores monetários
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

// Função para formatar percentuais
const formatPercentage = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    minimumFractionDigits: 2,
  }).format(value / 100)
}

// Componente para KPI Card
const KPICard = ({ 
  title, 
  value, 
  format, 
  trend, 
  icon: Icon 
}: { 
  title: string; 
  value: number; 
  format: 'currency' | 'percentage' | 'number';
  trend?: 'up' | 'down' | 'stable';
  icon: any;
}) => {
  const formatValue = () => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'percentage':
        return formatPercentage(value);
      default:
        return value.toLocaleString('pt-BR');
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="flex items-center space-x-1">
          <Icon className="h-4 w-4 text-muted-foreground" />
          {trend && getTrendIcon()}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatValue()}</div>
      </CardContent>
    </Card>
  );
};

export default function Dashboard() {
  const { dashboardData, loading, error, refetch } = useDashboard();
  const { health } = useHealthCheck();

  const handleRefetch = () => {
    refetch();
  };

  if (loading) {
    return (
      <LoadingSpinner 
        title="Carregando Dashboard Financeiro"
        description="Processando dados do Excel. Isso pode demorar alguns minutos na primeira execução."
        showProgress={true}
        progress={25} // Simulação de progresso
      />
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertDescription>
            Erro ao carregar dados: {error}
            <Button variant="outline" size="sm" onClick={handleRefetch} className="ml-2">
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const kpis = dashboardData?.kpis;
  const resumo = dashboardData?.resumo;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Financeiro</h1>
          <p className="text-muted-foreground">Visão geral do sistema financeiro</p>
        </div>
        <div className="flex items-center space-x-2">
          {health && (
            <Badge variant={health.status === 'healthy' ? 'success' : 'destructive'}>
              API {health.status === 'healthy' ? 'Online' : 'Offline'}
            </Badge>
          )}
          <Button onClick={handleRefetch}>Atualizar Dados</Button>
        </div>
      </div>

      <Separator className="mb-6" />

      {/* KPIs Principais */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <KPICard
            title="Receita Líquida"
            value={kpis.receita_liquida?.valor || 0}
            format="currency"
            trend={kpis.receita_liquida?.trend}
            icon={DollarSign}
          />
          <KPICard
            title="Lucro Líquido"
            value={kpis.lucro_liquido?.valor || 0}
            format="currency"
            trend={kpis.lucro_liquido?.trend}
            icon={TrendingUp}
          />
          <KPICard
            title="Margem Líquida"
            value={kpis.margem_liquida?.valor || 0}
            format="percentage"
            trend={kpis.margem_liquida?.trend}
            icon={Activity}
          />
          <KPICard
            title="Fluxo Operacional"
            value={kpis.fluxo_operacional?.valor || 0}
            format="currency"
            trend={kpis.fluxo_operacional?.trend}
            icon={DollarSign}
          />
        </div>
      )}

      {/* Cards de Navegação */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>DRE</CardTitle>
            <CardDescription>Demonstração do Resultado do Exercício</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Análise detalhada da demonstração de resultados
            </p>
            {resumo && (
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span>Receita Total:</span>
                  <span className="font-semibold">{formatCurrency(resumo.receita_total)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Lucro Total:</span>
                  <span className="font-semibold">{formatCurrency(resumo.lucro_total)}</span>
                </div>
              </div>
            )}
            <Button variant="outline" className="w-full">
              Ver DRE Completa
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>DFC</CardTitle>
            <CardDescription>Demonstração dos Fluxos de Caixa</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Análise dos fluxos de caixa operacionais
            </p>
            {resumo && (
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span>Fluxo Operacional:</span>
                  <span className="font-semibold">{formatCurrency(resumo.fluxo_operacional)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Margem Líquida:</span>
                  <span className="font-semibold">{formatPercentage(resumo.margem_liquida)}</span>
                </div>
              </div>
            )}
            <Button variant="outline" className="w-full">
              Ver DFC Completa
            </Button>
          </CardContent>
        </Card>

        <div className="flex">
          <Card>
            <CardHeader>
              <CardTitle>Demonstrativos Financeiros</CardTitle>
              <CardDescription>
                Análise detalhada de DRE e DFC com controles interativos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="dre" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="dre">DRE - Demonstração do Resultado</TabsTrigger>
                  <TabsTrigger value="dfc">DFC - Demonstração dos Fluxos de Caixa</TabsTrigger>
                </TabsList>
                
                <TabsContent value="dre" className="mt-6">
                  <DreTable />
                </TabsContent>
                
                <TabsContent value="dfc" className="mt-6">
                  <DfcTable />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>

    </div>
  )
} 