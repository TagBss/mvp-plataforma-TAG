import { useState, useEffect, useCallback } from 'react';
import { financialApi } from '../services/financial-api';
import {
  FinancialDataItem,
  FinancialDataFilters,
  FinancialDataByPeriod,
  FinancialSummary,
  CategoriesResponse,
  FinancialDataCreate,
  FinancialDataUpdate,
  HealthResponse
} from '../types/financial';

// Hook para dados financeiros
export const useFinancialData = (filters: FinancialDataFilters = {}) => {
  const [data, setData] = useState<FinancialDataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.getFinancialData(filters);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook para dados por período
export const useFinancialDataByPeriod = (
  periodType: string,
  startDate: string,
  endDate: string
) => {
  const [data, setData] = useState<FinancialDataByPeriod | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.getDataByPeriod(periodType, startDate, endDate);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados por período');
    } finally {
      setLoading(false);
    }
  }, [periodType, startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook para resumo por tipo
export const useFinancialSummary = (startDate: string, endDate: string) => {
  const [data, setData] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.getSummaryByType(startDate, endDate);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar resumo');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook para categorias
export const useCategories = () => {
  const [data, setData] = useState<CategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.getCategories();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar categorias');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook para health check
export const useHealthCheck = () => {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.getHealth();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao verificar saúde da API');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};

// Hook para operações CRUD
export const useFinancialDataCRUD = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createData = useCallback(async (data: FinancialDataCreate) => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.createFinancialData(data);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao criar dados';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateData = useCallback(async (id: number, data: FinancialDataUpdate) => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.updateFinancialData(id, data);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao atualizar dados';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteData = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await financialApi.deleteFinancialData(id);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao remover dados';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    createData,
    updateData,
    deleteData,
    loading,
    error
  };
};
