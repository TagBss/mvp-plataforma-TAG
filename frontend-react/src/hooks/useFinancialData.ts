import { useState, useEffect, useCallback } from 'react';
import { FinancialService } from '../services/financialService';
import type { 
  FilterParams, 
  KPIsData, 
  DREData, 
  DFCData,
  HealthResponse 
} from '../types/financial';

// Hook para gerenciar estado de loading e erro
export const useApiState = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeAsync = useCallback(async <T>(asyncFn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await asyncFn();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { loading, error, executeAsync, clearError };
};

// Hook para KPIs
export const useKPIs = (filters?: FilterParams) => {
  const [kpis, setKpis] = useState<KPIsData | null>(null);
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchKPIs = useCallback(async (newFilters?: FilterParams) => {
    const result = await executeAsync(() => 
      FinancialService.getKPIsCompletos(newFilters || filters)
    );
    if (result) {
      setKpis(result);
    }
  }, [filters, executeAsync]);

  useEffect(() => {
    fetchKPIs();
  }, [fetchKPIs]);

  return { 
    kpis, 
    loading, 
    error, 
    refetch: fetchKPIs, 
    clearError 
  };
};

// Hook para dados da DRE
export const useDRE = (filters?: FilterParams) => {
  const [dreData, setDreData] = useState<DREData | null>(null);
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchDRE = useCallback(async (newFilters?: FilterParams) => {
    const result = await executeAsync(() => 
      FinancialService.getDadosCompletos(newFilters || filters)
    );
    if (result) {
      setDreData(result.dre);
    }
  }, [filters, executeAsync]);

  useEffect(() => {
    fetchDRE();
  }, [fetchDRE]);

  return { 
    dreData, 
    loading, 
    error, 
    refetch: fetchDRE, 
    clearError 
  };
};

// Hook para dados da DFC
export const useDFC = (filters?: FilterParams) => {
  const [dfcData, setDfcData] = useState<DFCData | null>(null);
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchDFC = useCallback(async (newFilters?: FilterParams) => {
    const result = await executeAsync(() => 
      FinancialService.getDadosCompletos(newFilters || filters)
    );
    if (result) {
      setDfcData(result.dfc);
    }
  }, [filters, executeAsync]);

  useEffect(() => {
    fetchDFC();
  }, [fetchDFC]);

  return { 
    dfcData, 
    loading, 
    error, 
    refetch: fetchDFC, 
    clearError 
  };
};

// Hook para dados completos
export const useFinancialData = (filters?: FilterParams) => {
  const [data, setData] = useState<{
    dre: DREData | null;
    dfc: DFCData | null;
  }>({ dre: null, dfc: null });
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchData = useCallback(async (newFilters?: FilterParams) => {
    const result = await executeAsync(() => 
      FinancialService.getDadosCompletos(newFilters || filters)
    );
    if (result) {
      setData(result);
    }
  }, [filters, executeAsync]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    data, 
    loading, 
    error, 
    refetch: fetchData, 
    clearError 
  };
};

// Hook para dados do dashboard
export const useDashboard = (filters?: FilterParams) => {
  const [dashboardData, setDashboardData] = useState<{
    kpis: KPIsData;
    periodos: {
      meses: string[];
      anos: number[];
      trimestres: string[];
    };
    resumo: {
      receita_total: number;
      lucro_total: number;
      fluxo_operacional: number;
      margem_liquida: number;
    };
  } | null>(null);
  
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchDashboard = useCallback(async (newFilters?: FilterParams) => {
    const result = await executeAsync(() => 
      FinancialService.getDadosDashboard(newFilters || filters)
    );
    if (result) {
      setDashboardData(result);
    }
  }, [filters, executeAsync]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return { 
    dashboardData, 
    loading, 
    error, 
    refetch: fetchDashboard, 
    clearError 
  };
};

// Hook para períodos disponíveis
export const usePeriodos = () => {
  const [periodos, setPeriodos] = useState<{
    meses: string[];
    anos: number[];
    trimestres: string[];
  } | null>(null);
  
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchPeriodos = useCallback(async () => {
    const result = await executeAsync(() => 
      FinancialService.getPeriodosDisponiveis()
    );
    if (result) {
      setPeriodos(result);
    }
  }, [executeAsync]);

  useEffect(() => {
    fetchPeriodos();
  }, [fetchPeriodos]);

  return { 
    periodos, 
    loading, 
    error, 
    refetch: fetchPeriodos, 
    clearError 
  };
};

// Hook para verificar saúde da API
export const useHealthCheck = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const { loading, error, executeAsync, clearError } = useApiState();

  const checkHealth = useCallback(async () => {
    const result = await executeAsync(() => 
      FinancialService.verificarSaude()
    );
    if (result) {
      setHealth(result);
    }
  }, [executeAsync]);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return { 
    health, 
    loading, 
    error, 
    refetch: checkHealth, 
    clearError 
  };
};

// Hook para dados de tendência
export const useTendencia = (conta: string, tipo: 'dre' | 'dfc') => {
  const [tendencia, setTendencia] = useState<{
    meses: string[];
    valores_real: number[];
    valores_orc: number[];
  } | null>(null);
  
  const { loading, error, executeAsync, clearError } = useApiState();

  const fetchTendencia = useCallback(async (newConta?: string, newTipo?: 'dre' | 'dfc') => {
    const result = await executeAsync(() => 
      FinancialService.getDadosTendencia(newConta || conta, newTipo || tipo)
    );
    if (result) {
      setTendencia(result);
    }
  }, [conta, tipo, executeAsync]);

  useEffect(() => {
    if (conta) {
      fetchTendencia();
    }
  }, [fetchTendencia, conta]);

  return { 
    tendencia, 
    loading, 
    error, 
    refetch: fetchTendencia, 
    clearError 
  };
};
