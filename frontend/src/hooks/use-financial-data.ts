import { useState, useEffect } from 'react';
import { apiCache } from '@/lib/api-cache';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Tipos das respostas da API
export type MoMData = {
  mes: string;
  valor_atual: number;
  valor_anterior: number | null;
  variacao_absoluta: number | null;
  variacao_percentual: number | null;
};

export type SaldoResponse = {
  success: boolean;
  data: {
    saldo_total: number;
    mom_analysis: MoMData[];
    meses_disponiveis: string[];
    pmr?: string;
    pmp?: string;
  };
};

export type MovimentacoesResponse = {
  success: boolean;
  data: {
    saldo_total: number;
    mom_analysis: MoMData[];
  };
};

export type SaldosEvolucaoResponse = {
  success: boolean;
  data: {
    evolucao: Array<{
      mes: string;
      saldo_inicial: number;
      movimentacao: number;
      saldo_final: number;
      variacao_absoluta?: number | null;
      variacao_percentual?: number | null;
    }>;
  };
};

export type CustosResponse = {
  success: boolean;
  data: {
    total_geral: number;
    total_geral_classificacao: Record<string, number>;
    custos_mes: Record<string, number>;
    custos_mes_classificacao: Record<string, Record<string, number>>;
  };
};

export type DreResponse = {
  meses: string[];
  trimestres: string[];
  anos: number[];
  data: Array<{
    tipo: string;
    nome: string;
    valores_mensais?: Record<string, number>;
    // ... outras propriedades da DRE
  }>;
};

export type DfcResponse = {
  meses: string[];
  trimestres: string[];
  anos: number[];
  data: Array<{
    tipo: string;
    nome: string;
    valores_mensais?: Record<string, number>;
    // ... outras propriedades da DFC
  }>;
};

// Hook principal para dados financeiros
export function useFinancialData() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estados dos dados
  const [saldoReceber, setSaldoReceber] = useState<SaldoResponse | null>(null);
  const [saldoPagar, setSaldoPagar] = useState<SaldoResponse | null>(null);
  const [movimentacoes, setMovimentacoes] = useState<MovimentacoesResponse | null>(null);
  const [saldosEvolucao, setSaldosEvolucao] = useState<SaldosEvolucaoResponse | null>(null);
  const [custos, setCustos] = useState<CustosResponse | null>(null);
  const [dreData, setDreData] = useState<DreResponse | null>(null);
  const [dfcData, setDfcData] = useState<DfcResponse | null>(null);

  // Função para carregar dados básicos (sem filtro de mês)
  const loadBasicData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [receberRes, pagarRes, saldosRes] = await Promise.all([
        apiCache.fetchWithCache<SaldoResponse>(`${API_BASE_URL}/receber`),
        apiCache.fetchWithCache<SaldoResponse>(`${API_BASE_URL}/pagar`),
        apiCache.fetchWithCache<SaldosEvolucaoResponse>(`${API_BASE_URL}/saldos-evolucao`),
      ]);

      setSaldoReceber(receberRes);
      setSaldoPagar(pagarRes);
      setSaldosEvolucao(saldosRes);

      return {
        mesesDisponiveis: receberRes.data?.meses_disponiveis || [],
        pmr: receberRes.data?.pmr,
        pmp: pagarRes.data?.pmp,
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados básicos');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Função para carregar dados filtrados por mês
  const loadDataByMonth = async (mes: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const queryString = mes ? `?mes=${mes}` : '';
      
      const [receberRes, pagarRes, movRes, custosRes] = await Promise.all([
        apiCache.fetchWithCache<SaldoResponse>(`${API_BASE_URL}/receber${queryString}`),
        apiCache.fetchWithCache<SaldoResponse>(`${API_BASE_URL}/pagar${queryString}`),
        apiCache.fetchWithCache<MovimentacoesResponse>(`${API_BASE_URL}/movimentacoes${queryString}`),
        apiCache.fetchWithCache<CustosResponse>(`${API_BASE_URL}/custos-visao-financeiro`),
      ]);

      setSaldoReceber(receberRes);
      setSaldoPagar(pagarRes);
      setMovimentacoes(movRes);
      setCustos(custosRes);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados do mês');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Função para carregar dados da DRE
  const loadDreData = async () => {
    try {
      const dreRes = await apiCache.fetchWithCache<DreResponse>(`${API_BASE_URL}/dre`);
      setDreData(dreRes);
      return dreRes;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados da DRE');
      throw err;
    }
  };

  // Função para carregar dados da DFC
  const loadDfcData = async () => {
    try {
      const dfcRes = await apiCache.fetchWithCache<DfcResponse>(`${API_BASE_URL}/dfc`);
      setDfcData(dfcRes);
      return dfcRes;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados da DFC');
      throw err;
    }
  };

  // Função para limpar cache
  const clearCache = () => {
    apiCache.clear();
  };

  return {
    // Estados
    isLoading,
    error,
    saldoReceber,
    saldoPagar,
    movimentacoes,
    saldosEvolucao,
    custos,
    dreData,
    dfcData,

    // Métodos
    loadBasicData,
    loadDataByMonth,
    loadDreData,
    loadDfcData,
    clearCache,
  };
}

// Hook específico para KPIs financeiros
export function useKpisFinanceiro(mesSelecionado: string | null) {
  const {
    isLoading,
    error,
    saldoReceber,
    saldoPagar,
    movimentacoes,
    saldosEvolucao,
    custos,
    loadBasicData,
    loadDataByMonth,
  } = useFinancialData();

  const [inicializado, setInicializado] = useState(false);

  // Carregar dados básicos na inicialização
  useEffect(() => {
    if (!inicializado) {
      loadBasicData()
        .then(() => setInicializado(true))
        .catch(console.error);
    }
  }, [inicializado, loadBasicData]);

  // Carregar dados por mês quando o mês muda
  useEffect(() => {
    if (inicializado && mesSelecionado !== null) {
      loadDataByMonth(mesSelecionado).catch(console.error);
    }
  }, [inicializado, mesSelecionado, loadDataByMonth]);

  return {
    isLoading,
    error,
    inicializado,
    saldoReceber,
    saldoPagar,
    movimentacoes,
    saldosEvolucao,
    custos,
  };
}
