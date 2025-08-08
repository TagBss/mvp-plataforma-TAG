import { api } from './api';
import {
  FinancialDataItem,
  FinancialDataFilters,
  FinancialDataByPeriod,
  FinancialSummary,
  CategoriesResponse,
  FinancialDataCreate,
  FinancialDataUpdate,
  HealthResponse,
  ApiResponse
} from '../types/financial';

// Endpoints para dados financeiros PostgreSQL
export const financialApi = {
  // Buscar dados financeiros com filtros
  getFinancialData: async (filters: FinancialDataFilters = {}): Promise<FinancialDataItem[]> => {
    const params = new URLSearchParams();
    
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.category) params.append('category', filters.category);
    if (filters.data_type) params.append('data_type', filters.data_type);
    if (filters.is_budget !== undefined) params.append('is_budget', filters.is_budget.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    
    const response = await api.get(`/financial-data/?${params.toString()}`);
    return response.data;
  },

  // Buscar dados agrupados por período
  getDataByPeriod: async (
    periodType: string,
    startDate: string,
    endDate: string
  ): Promise<FinancialDataByPeriod> => {
    const response = await api.get('/financial-data/by-period', {
      params: {
        period_type: periodType,
        start_date: startDate,
        end_date: endDate
      }
    });
    return response.data;
  },

  // Buscar resumo por tipo
  getSummaryByType: async (startDate: string, endDate: string): Promise<FinancialSummary> => {
    const response = await api.get('/financial-data/summary', {
      params: {
        start_date: startDate,
        end_date: endDate
      }
    });
    return response.data;
  },

  // Buscar hierarquia de categorias
  getCategories: async (): Promise<CategoriesResponse> => {
    const response = await api.get('/financial-data/categories');
    return response.data;
  },

  // Criar novo registro financeiro
  createFinancialData: async (data: FinancialDataCreate): Promise<FinancialDataItem> => {
    const response = await api.post('/financial-data/', data);
    return response.data;
  },

  // Atualizar registro financeiro
  updateFinancialData: async (id: number, data: FinancialDataUpdate): Promise<FinancialDataItem> => {
    const response = await api.put(`/financial-data/${id}`, data);
    return response.data;
  },

  // Remover registro financeiro
  deleteFinancialData: async (id: number): Promise<{ message: string }> => {
    const response = await api.delete(`/financial-data/${id}`);
    return response.data;
  },

  // Health check
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get('/financial-data/health');
    return response.data;
  }
};

// Função helper para formatar datas
export const formatDate = (date: string | Date): string => {
  if (typeof date === 'string') {
    return date;
  }
  return date.toISOString().split('T')[0];
};

// Função helper para formatar valores monetários
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
};

// Função para formatar no estilo curto (Mil / Mi)
export const formatCurrencyShort = (value: number, opts?: { noPrefix?: boolean }): string => {
  const absValue = Math.abs(value);
  let formatted = "";

  if (absValue >= 1_000_000) {
    formatted = `${(absValue / 1_000_000).toFixed(1)} Mi`;
  } else if (absValue >= 1_000) {
    formatted = `${(absValue / 1_000).toFixed(1)} Mil`;
  } else {
    formatted = absValue.toFixed(0);
  }

  const prefix = opts?.noPrefix ? "" : "R$ ";
  return `${prefix}${value < 0 ? "-" : ""}${formatted.replace(".", ",")}`;
};

// Função helper para formatar percentuais
export const formatPercentage = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value / 100);
};

// Função helper para calcular totais
export const calculateTotals = (data: FinancialDataItem[]): Record<string, number> => {
  const totals: Record<string, number> = {};
  
  data.forEach(item => {
    if (!totals[item.type]) {
      totals[item.type] = 0;
    }
    totals[item.type] += item.value;
  });
  
  return totals;
};

// Função helper para agrupar dados por categoria
export const groupByCategory = (data: FinancialDataItem[]): Record<string, number> => {
  const grouped: Record<string, number> = {};
  
  data.forEach(item => {
    if (!grouped[item.category]) {
      grouped[item.category] = 0;
    }
    grouped[item.category] += item.value;
  });
  
  return grouped;
};

// Função helper para filtrar dados por período
export const filterByDateRange = (
  data: FinancialDataItem[],
  startDate: string,
  endDate: string
): FinancialDataItem[] => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  return data.filter(item => {
    const itemDate = new Date(item.date);
    return itemDate >= start && itemDate <= end;
  });
};

// Função helper para obter tipos únicos
export const getUniqueTypes = (data: FinancialDataItem[]): string[] => {
  const types = new Set(data.map(item => item.type));
  return Array.from(types);
};

// Função helper para obter categorias únicas
export const getUniqueCategories = (data: FinancialDataItem[]): string[] => {
  const categories = new Set(data.map(item => item.category));
  return Array.from(categories);
};
