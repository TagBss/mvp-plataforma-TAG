import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useFinancialData, useFinancialSummary, useCategories } from '../hooks/use-financial-data';
import { FinancialDataFilters, FinancialDataItem } from '../types/financial';

interface FinancialDataContextType {
  // Dados compartilhados
  financialData: FinancialDataItem[];
  summary: any;
  categories: any;
  
  // Estados de loading
  dataLoading: boolean;
  summaryLoading: boolean;
  categoriesLoading: boolean;
  
  // Estados de erro
  dataError: string | null;
  summaryError: string | null;
  categoriesError: string | null;
  
  // Filtros atuais
  currentFilters: FinancialDataFilters;
  
  // Funções para atualizar filtros
  updateFilters: (filters: Partial<FinancialDataFilters>) => void;
  setDateRange: (startDate: string, endDate: string) => void;
  
  // Funções para refetch
  refetchData: () => void;
  refetchSummary: () => void;
  refetchCategories: () => void;
}

const FinancialDataContext = createContext<FinancialDataContextType | undefined>(undefined);

interface FinancialDataProviderProps {
  children: ReactNode;
  initialFilters?: FinancialDataFilters;
}

export const FinancialDataProvider: React.FC<FinancialDataProviderProps> = ({ 
  children, 
  initialFilters = {} 
}) => {
  const [filters, setFilters] = useState<FinancialDataFilters>({
    start_date: "2024-01-01", // Usar 2024 para dados de teste
    end_date: "2024-12-31",   // Usar 2024 para dados de teste
    ...initialFilters
  });

  // Hooks para buscar dados
  const { 
    data: financialData, 
    loading: dataLoading, 
    error: dataError, 
    refetch: refetchData 
  } = useFinancialData(filters);

  const { 
    data: summary, 
    loading: summaryLoading, 
    error: summaryError, 
    refetch: refetchSummary 
  } = useFinancialSummary(filters.start_date!, filters.end_date!);

  const { 
    data: categories, 
    loading: categoriesLoading, 
    error: categoriesError, 
    refetch: refetchCategories 
  } = useCategories();

  // Função para atualizar filtros
  const updateFilters = (newFilters: Partial<FinancialDataFilters>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }));
  };

  // Função para definir range de datas
  const setDateRange = (startDate: string, endDate: string) => {
    setFilters(prev => ({
      ...prev,
      start_date: startDate,
      end_date: endDate
    }));
  };

  const contextValue: FinancialDataContextType = {
    financialData,
    summary,
    categories,
    dataLoading,
    summaryLoading,
    categoriesLoading,
    dataError,
    summaryError,
    categoriesError,
    currentFilters: filters,
    updateFilters,
    setDateRange,
    refetchData,
    refetchSummary,
    refetchCategories
  };

  return (
    <FinancialDataContext.Provider value={contextValue}>
      {children}
    </FinancialDataContext.Provider>
  );
};

// Hook para usar o contexto
export const useFinancialDataContext = () => {
  const context = useContext(FinancialDataContext);
  if (context === undefined) {
    throw new Error('useFinancialDataContext must be used within a FinancialDataProvider');
  }
  return context;
};
