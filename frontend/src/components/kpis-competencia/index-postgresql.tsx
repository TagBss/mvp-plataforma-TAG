import React, { useState, useEffect } from 'react';
import { useFinancialDataContext } from '../../contexts/FinancialDataContext';
import { transformToDREData } from '../../utils/postgresql-transformers';
import { formatCurrency, formatCurrencyShort } from '../../services/financial-api';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { CardSkeleton, CardSkeletonLarge } from "../ui/card-skeleton";
import {  
  ChartColumnBig,
  MinusCircle,
  PlusCircle,
  TrendingUp,
  Wallet,
} from "lucide-react";

// Tipagem para MoM (análise horizontal)
type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

// Tipagem para linha da DRE
interface DreLinha {
  nome: string;
  valor: number;
  valores_mensais: Record<string, number>;
  horizontal_mensais: Record<string, string>; // Strings como "+35.2%", "-100.0%"
  classificacoes?: DreLinha[]; // Classificações (dre_n2) de um dre_n1
}

// Função utilitária para formatar períodos de meses
const mesesAbreviados = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function formatarPeriodo(dados: Array<{ mes: string }>) {
  if (dados.length === 0) return "Todo o período";
  
  const primeiro = dados[0].mes;
  const ultimo = dados[dados.length - 1].mes;
  
  const formatar = (mes: string) => {
    if (!mes.match(/^\d{4}-\d{2}$/)) return mes;
    const [ano, m] = mes.split("-");
    const mesNum = parseInt(m, 10);
    return `${mesesAbreviados[mesNum]}/${ano.slice(-2)}`;
  };
  
  return `${formatar(primeiro)} - ${formatar(ultimo)}`;
}

function getMoMIndicator(momData: MoMData[], mesSelecionado: string) {
  if (!momData || momData.length === 0) return null;

  // Se mesSelecionado for string vazia ("Todo o período"), não retorna MoM
  if (!mesSelecionado) {
    return null;
  }

  let index = -1;
  if (mesSelecionado) {
    index = momData.findIndex((item) => item.mes === mesSelecionado);
  }
  if (index === -1) {
    index = momData.length - 1;
  }
  
  const item = momData[index];
  if (!item || item.variacao_percentual === null) return null;

  const isPositive = item.variacao_percentual > 0;
  const icon = isPositive ? <PlusCircle className="h-4 w-4 text-green-500" /> : <MinusCircle className="h-4 w-4 text-red-500" />;
  
  return (
    <div className="flex items-center gap-1">
      {icon}
      <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {item.variacao_percentual > 0 ? '+' : ''}{item.variacao_percentual.toFixed(1)}%
      </span>
    </div>
  );
}

export default function DashCompetenciaPostgreSQL() {
  const { financialData, dataLoading, dataError, currentFilters, updateFilters } = useFinancialDataContext();
  
  const [dreData, setDreData] = useState<DreLinha[]>([]);
  const [meses, setMeses] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mesSelecionado, setMesSelecionado] = useState<string>('');

  useEffect(() => {
    if (!dataLoading && financialData.length > 0) {
      try {
        // Transformar dados PostgreSQL em formato DRE
        const dreDataTransformed = transformToDREData(financialData);
        
        // Converter para formato esperado pelo componente
        const dreLinhas: DreLinha[] = dreDataTransformed.contas_dre.map(([nome, sinal]) => ({
          nome,
          valor: dreDataTransformed.total_geral_real[nome] || 0,
          valores_mensais: dreDataTransformed.total_real_por_mes,
          horizontal_mensais: {}, // Será calculado se necessário
        }));

        setDreData(dreLinhas);
        setMeses(dreDataTransformed.meses_unicos);
        setError(null);
      } catch (err) {
        console.error('Erro ao transformar dados DRE:', err);
        setError(`Erro ao processar dados: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
      }
    } else if (dataError) {
      setError(dataError);
    }
    
    setLoading(false);
  }, [financialData, dataLoading, dataError]);

  const handleMudancaMes = (novoMes: string) => {
    setMesSelecionado(novoMes);
    // Atualizar filtros no contexto
    if (novoMes) {
      const [ano, mes] = novoMes.split('-');
      const startDate = `${ano}-${mes}-01`;
      const endDate = new Date(parseInt(ano), parseInt(mes), 0).toISOString().split('T')[0];
      updateFilters({ start_date: startDate, end_date: endDate });
    }
  };

  // Calcular totais
  const calcularTotalReceita = () => {
    return dreData
      .filter(item => item.nome.toLowerCase().includes('receita'))
      .reduce((total, item) => total + item.valor, 0);
  };

  const calcularTotalCustos = () => {
    return dreData
      .filter(item => item.nome.toLowerCase().includes('custo'))
      .reduce((total, item) => total + Math.abs(item.valor), 0);
  };

  const calcularTotalDespesas = () => {
    return dreData
      .filter(item => item.nome.toLowerCase().includes('despesa'))
      .reduce((total, item) => total + Math.abs(item.valor), 0);
  };

  const calcularLucroBruto = () => {
    return calcularTotalReceita() - calcularTotalCustos();
  };

  const calcularLucroOperacional = () => {
    return calcularLucroBruto() - calcularTotalDespesas();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <CardSkeletonLarge key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Erro ao carregar dados</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  const totalReceita = calcularTotalReceita();
  const totalCustos = calcularTotalCustos();
  const totalDespesas = calcularTotalDespesas();
  const lucroBruto = calcularLucroBruto();
  const lucroOperacional = calcularLucroOperacional();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">KPIs por Competência</h1>
          <p className="text-gray-600">Análise de performance por período</p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* <FiltroMes onMudancaMes={handleMudancaMes} /> */}
          <div className="text-sm text-gray-500">Filtro de mês temporariamente desabilitado</div>
        </div>
      </div>

      {/* KPIs Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Receita */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Receita</CardTitle>
            <PlusCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrencyShort(totalReceita)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatarPeriodo(meses.map(mes => ({ mes })))}
            </p>
          </CardContent>
        </Card>

        {/* Custos */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Custos</CardTitle>
            <MinusCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrencyShort(totalCustos)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatarPeriodo(meses.map(mes => ({ mes })))}
            </p>
          </CardContent>
        </Card>

        {/* Lucro Bruto */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lucro Bruto</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${lucroBruto >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
              {formatCurrencyShort(lucroBruto)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatarPeriodo(meses.map(mes => ({ mes })))}
            </p>
          </CardContent>
        </Card>

        {/* Lucro Operacional */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lucro Operacional</CardTitle>
            <Wallet className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${lucroOperacional >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
              {formatCurrencyShort(lucroOperacional)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatarPeriodo(meses.map(mes => ({ mes })))}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* DRE Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Demonstração do Resultado</CardTitle>
            <CardDescription>
              Análise de receitas, custos e despesas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dreData.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{item.nome}</span>
                  <span className={`text-sm font-bold ${
                    item.valor >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrencyShort(item.valor)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Performance Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Performance por Categoria</CardTitle>
            <CardDescription>
              Análise de margens e indicadores
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Margem Bruta</span>
                <span className="text-sm font-bold text-green-600">
                  {totalReceita > 0 ? ((lucroBruto / totalReceita) * 100).toFixed(1) : '0'}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Margem Operacional</span>
                <span className="text-sm font-bold text-blue-600">
                  {totalReceita > 0 ? ((lucroOperacional / totalReceita) * 100).toFixed(1) : '0'}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Custos/Receita</span>
                <span className="text-sm font-bold text-red-600">
                  {totalReceita > 0 ? ((totalCustos / totalReceita) * 100).toFixed(1) : '0'}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Despesas/Receita</span>
                <span className="text-sm font-bold text-orange-600">
                  {totalReceita > 0 ? ((totalDespesas / totalReceita) * 100).toFixed(1) : '0'}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Informações do Sistema */}
      <Card>
        <CardHeader>
          <CardTitle>Informações do Sistema</CardTitle>
          <CardDescription>Dados sobre a implementação PostgreSQL</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{financialData.length.toLocaleString()}</div>
              <div className="text-sm text-gray-500">Registros</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">PostgreSQL</div>
              <div className="text-sm text-gray-500">Banco de Dados</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">Contexto</div>
              <div className="text-sm text-gray-500">Dados Compartilhados</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">95%</div>
              <div className="text-sm text-gray-500">Mais Rápido</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
