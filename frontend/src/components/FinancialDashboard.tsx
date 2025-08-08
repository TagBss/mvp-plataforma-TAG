import React, { useState } from 'react';
import { useFinancialSummary, useHealthCheck } from '../hooks/use-financial-data';
import { formatCurrency } from '../services/financial-api';

export const FinancialDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState({
    startDate: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0], // 1º de janeiro do ano atual
    endDate: new Date().toISOString().split('T')[0] // Hoje
  });

  const { data: summary, loading: summaryLoading, error: summaryError } = useFinancialSummary(
    dateRange.startDate,
    dateRange.endDate
  );

  const { data: health, loading: healthLoading } = useHealthCheck();

  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard Financeiro</h1>
            <p className="text-gray-600">Análise dos dados financeiros PostgreSQL</p>
          </div>
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Data Inicial</label>
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) => handleDateChange('startDate', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Data Final</label>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) => handleDateChange('endDate', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Health Status */}
      {health && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Status do Sistema</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                health.status === 'healthy' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {health.status === 'healthy' ? '✅ Saudável' : '❌ Problema'}
              </div>
              <div className="text-xs text-gray-500 mt-1">Status</div>
            </div>
            <div className="text-center">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                health.database_connected 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {health.database_connected ? '✅ Conectado' : '❌ Desconectado'}
              </div>
              <div className="text-xs text-gray-500 mt-1">Banco de Dados</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {health.records_count.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">Registros</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-900">
                {new Date(health.timestamp).toLocaleString('pt-BR')}
              </div>
              <div className="text-xs text-gray-500">Última Verificação</div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Resumo por Tipo</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(summary.summary).map(([type, value]) => (
              <div key={type} className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatCurrency(value)}
                </div>
                <div className="text-sm text-gray-500 capitalize">{type}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {dateRange.startDate} a {dateRange.endDate}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {(summaryLoading || healthLoading) && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Carregando dados...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {summaryError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro ao carregar resumo</h3>
              <div className="mt-2 text-sm text-red-700">{summaryError}</div>
            </div>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Informações do Sistema</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Backend:</span>
              <span className="text-sm font-medium text-gray-900">PostgreSQL + FastAPI</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Frontend:</span>
              <span className="text-sm font-medium text-gray-900">React + TypeScript</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">ORM:</span>
              <span className="text-sm font-medium text-gray-900">SQLAlchemy</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Dados Migrados:</span>
              <span className="text-sm font-medium text-gray-900">15.338 registros</span>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Endpoints Disponíveis</h3>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="font-medium text-gray-900">GET</span>
              <span className="text-gray-600 ml-2">/financial-data/</span>
            </div>
            <div className="text-sm">
              <span className="font-medium text-gray-900">GET</span>
              <span className="text-gray-600 ml-2">/financial-data/by-period</span>
            </div>
            <div className="text-sm">
              <span className="font-medium text-gray-900">GET</span>
              <span className="text-gray-600 ml-2">/financial-data/summary</span>
            </div>
            <div className="text-sm">
              <span className="font-medium text-gray-900">GET</span>
              <span className="text-gray-600 ml-2">/financial-data/categories</span>
            </div>
            <div className="text-sm">
              <span className="font-medium text-gray-900">GET</span>
              <span className="text-gray-600 ml-2">/financial-data/health</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
