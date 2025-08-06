import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "../ui/card";
import { Button } from "../ui/button";
import { TrendingUp, TrendingDown, Wallet, Package, ArrowUpDown, Hourglass, PlusCircle, MinusCircle, AlertTriangle, RefreshCw } from "lucide-react";
import { formatCurrencyShort } from "../../utils/formatters";
import { ChartAreaSaldoFinal } from "../charts-financeiro/chart-area-saldo-final";
import { ChartCustosFinanceiro } from "../charts-financeiro/chart-bar-custos";
import ChartMovimentacoes from "../charts-financeiro/chart-movimentacoes";
import { FiltroMes } from "../filtro-mes";
import { api } from "../../services/api";
import { ErrorBoundary, FinancialDataErrorFallback } from '../error-boundary';
import { DashboardSkeleton, KPIsSkeleton, ChartSkeleton, FinancialTableSkeleton } from '../loading-skeletons';
import { useToast, useFinancialToast } from '../toast';

// Tipos
type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

type SaldoData = {
  success: boolean;
  data: {
    saldo_total: number;
    mom_analysis: MoMData[];
    meses_disponiveis?: string[];
    pmr?: string;
    pmp?: string;
  };
};

type DFCItem = {
  tipo: string;
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  horizontal_mensais: Record<string, string>;
  classificacoes?: any[];
};

type DFCData = {
  success?: boolean;
  meses: string[];
  trimestres: string[];
  anos: number[];
  data: DFCItem[];
};

// Hook para gerenciar estados de carregamento dos dados financeiros
export function useFinancialDataState() {
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const financialToast = useFinancialToast();

  const startLoading = () => {
    setIsLoading(true);
    setHasError(false);
    setError(null);
  };

  const stopLoading = () => {
    setIsLoading(false);
  };

  const handleError = (error: Error | string) => {
    const errorObj = typeof error === 'string' ? new Error(error) : error;
    setError(errorObj);
    setHasError(true);
    setIsLoading(false);
    financialToast.dataError(errorObj.message);
  };

  const handleSuccess = (message?: string, count?: number) => {
    setHasError(false);
    setError(null);
    setIsLoading(false);
    
    if (message && count !== undefined) {
      financialToast.dataLoaded(count);
    }
  };

  const retry = () => {
    setHasError(false);
    setError(null);
  };

  return {
    isLoading,
    hasError,
    error,
    startLoading,
    stopLoading,
    handleError,
    handleSuccess,
    retry
  };
}

// Componente KPI melhorado com error handling
export function KPICardWithErrorHandling({
  title,
  value,
  description,
  icon: Icon,
  trend,
  isLoading = false,
  error
}: {
  title: string;
  value: string | number;
  description?: string;
  icon?: any;
  trend?: 'up' | 'down' | 'neutral';
  isLoading?: boolean;
  error?: Error | null;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="h-4 w-[100px] bg-muted animate-pulse rounded" />
          <div className="h-4 w-4 bg-muted animate-pulse rounded" />
        </CardHeader>
        <CardContent>
          <div className="h-8 w-[120px] bg-muted animate-pulse rounded mb-1" />
          <div className="h-3 w-[80px] bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="p-6 text-center">
          <AlertTriangle className="mx-auto h-6 w-6 text-destructive mb-2" />
          <p className="text-sm text-destructive">Erro ao carregar {title}</p>
        </CardContent>
      </Card>
    );
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return Icon ? <Icon className="h-4 w-4" /> : null;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {getTrendIcon()}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

// Fallback específico para gráficos
function ChartErrorFallback({ resetError }: { resetError: () => void }) {
  return (
    <Card className="border-destructive">
      <CardContent className="p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-destructive mb-2" />
        <p className="text-sm text-muted-foreground mb-4">
          Erro ao carregar gráfico
        </p>
        <Button size="sm" onClick={resetError}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Tentar Novamente
        </Button>
      </CardContent>
    </Card>
  );
}

// Componente principal melhorado
export default function DashFinanceiro() {
  const financialState = useFinancialDataState();
  const financialToast = useFinancialToast();
  const toast = useToast();

  // Estados dos dados
  const [saldoReceber, setSaldoReceber] = useState<SaldoData | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<SaldoData | null>(null);
  const [dfcData, setDfcData] = useState<DFCData | null>(null);
  const [mesSelecionado, setMesSelecionado] = useState<string | null>(null);
  const [inicializado, setInicializado] = useState(false);

  // Função para carregar dados
  const carregarDados = async () => {
    if (!inicializado || mesSelecionado === null || mesSelecionado === undefined) {
      return;
    }

    try {
      financialState.startLoading();
      
      const queryString = mesSelecionado ? `?mes=${mesSelecionado}` : '';
      
      const [receberRes, pagarRes, dfcRes] = await Promise.all([
        api.get(`/receber${queryString}`),
        api.get(`/pagar${queryString}`),
        api.get('/dfc')
      ]);

      setSaldoReceber(receberRes.data);
      setSaldoPagar(pagarRes.data);
      setDfcData(dfcRes.data);

      // Success toast
      const totalRegistros = (receberRes.data?.data?.mom_analysis?.length || 0) + 
                           (pagarRes.data?.data?.mom_analysis?.length || 0) + 
                           (dfcRes.data?.data?.length || 0);
      
      financialState.handleSuccess('Dados carregados', totalRegistros);
      
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      financialState.handleError(error as Error);
    }
  };

  // Inicialização
  useEffect(() => {
    const mesesDisponiveis = ['2024-12', '2024-11', '2024-10', '2024-09', '2024-08'];
    if (!inicializado) {
      setMesSelecionado(mesesDisponiveis[0]);
      setInicializado(true);
    }
  }, [inicializado]);

  // Carregar dados quando mês muda
  useEffect(() => {
    carregarDados();
  }, [mesSelecionado, inicializado]);

  // Manipulador de mudança de mês
  const handleMesChange = (novoMes: string) => {
    setMesSelecionado(novoMes);
    toast.info(`Carregando dados para ${novoMes}...`);
  };

  // Se está carregando, mostrar skeleton
  if (financialState.isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <ErrorBoundary fallback={FinancialDataErrorFallback}>
      <div className="space-y-6 p-6">
        {/* Header com filtros */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Dashboard Financeiro</h1>
          <FiltroMes 
            value={mesSelecionado || ''} 
            onSelect={handleMesChange}
            endpoint="receber"
          />
        </div>

        {/* KPIs Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KPICardWithErrorHandling
            title="Contas a Receber"
            value={saldoReceber?.data?.saldo_total ? 
              formatCurrencyShort(saldoReceber.data.saldo_total) : '--'}
            description={saldoReceber?.data?.pmr ? `PMR: ${saldoReceber.data.pmr}` : ''}
            icon={TrendingUp}
            trend="up"
            isLoading={financialState.isLoading}
            error={financialState.error}
          />
          
          <KPICardWithErrorHandling
            title="Contas a Pagar"
            value={saldoPagar?.data?.saldo_total ? 
              formatCurrencyShort(saldoPagar.data.saldo_total) : '--'}
            description={saldoPagar?.data?.pmp ? `PMP: ${saldoPagar.data.pmp}` : ''}
            icon={TrendingDown}
            trend="down"
            isLoading={financialState.isLoading}
            error={financialState.error}
          />

          <KPICardWithErrorHandling
            title="Saldo Líquido"
            value={saldoReceber?.data?.saldo_total && saldoPagar?.data?.saldo_total ? 
              formatCurrencyShort(saldoReceber.data.saldo_total - saldoPagar.data.saldo_total) : '--'}
            description="Disponível hoje"
            icon={Wallet}
            trend="neutral"
            isLoading={financialState.isLoading}
            error={financialState.error}
          />

          <KPICardWithErrorHandling
            title="Fluxo do Mês"
            value="--"
            description="Previsão mensal"
            icon={ArrowUpDown}
            trend="neutral"
            isLoading={financialState.isLoading}
            error={financialState.error}
          />
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 md:grid-cols-2">
          <ErrorBoundary fallback={ChartErrorFallback}>
            {financialState.isLoading ? (
              <ChartSkeleton />
            ) : (
              saldoReceber?.data?.mom_analysis && (
                <ChartAreaSaldoFinal 
                  data={saldoReceber.data.mom_analysis.map(item => ({
                    mes: item.mes,
                    saldo_final: item.valor_atual
                  }))} 
                  mesSelecionado={mesSelecionado || ''}
                />
              )
            )}
          </ErrorBoundary>

          <ErrorBoundary fallback={ChartErrorFallback}>
            {financialState.isLoading ? (
              <ChartSkeleton />
            ) : (
              <ChartMovimentacoes 
                mesSelecionado={mesSelecionado || ''}
                momReceber={saldoReceber?.data?.mom_analysis}
                momPagar={saldoPagar?.data?.mom_analysis}
              />
            )}
          </ErrorBoundary>
        </div>

        {/* Error state retry button */}
        {financialState.hasError && (
          <div className="text-center py-8">
            <Button onClick={() => {
              financialState.retry();
              carregarDados();
            }}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Tentar Carregar Novamente
            </Button>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
