// Tipos base para dados financeiros
export interface FinancialData {
  meses_unicos: string[];
  anos_unicos: number[];
  trimestres_unicos: string[];
  total_real_por_mes: Record<string, Record<string, number>>;
  total_orc_por_mes: Record<string, Record<string, number>>;
  total_real_por_tri: Record<string, Record<string, number>>;
  total_orc_por_tri: Record<string, Record<string, number>>;
  total_real_por_ano: Record<number, Record<string, number>>;
  total_orc_por_ano: Record<number, Record<string, number>>;
  total_geral_real: Record<string, number>;
  total_geral_orc: Record<string, number>;
}

// Tipos específicos para DRE
export interface DREData extends FinancialData {
  contas_dre: Array<[string, string]>; // [nome_conta, sinal]
  estrutura_hierarquica: DREHierarchy[];
  analise_vertical: Record<string, Record<string, number>>;
  analise_horizontal: Record<string, Record<string, number>>;
  realizado_vs_orcado: Record<string, Record<string, number>>;
  totalizadores: Record<string, number>;
}

export interface DREHierarchy {
  id: string;
  nome: string;
  nivel: number;
  pai?: string;
  valor_real: number;
  valor_orc: number;
  children?: DREHierarchy[];
}

// Tipos específicos para DFC
export interface DFCData extends FinancialData {
  contas_dfc: Array<[string, string]>; // [nome_conta, sinal]
  estrutura_hierarquica: DFCHierarchy[];
  analise_vertical: Record<string, Record<string, number>>;
  analise_horizontal: Record<string, Record<string, number>>;
  realizado_vs_orcado: Record<string, Record<string, number>>;
  totalizadores: Record<string, number>;
  saldo_inicial: Record<string, number>;
  saldo_final: Record<string, number>;
}

export interface DFCHierarchy {
  id: string;
  nome: string;
  nivel: number;
  pai?: string;
  valor_real: number;
  valor_orc: number;
  children?: DFCHierarchy[];
}

// Tipos para filtros
export interface PeriodFilter {
  mes?: string; // formato: "2024-01"
  trimestre?: string; // formato: "2024-T1"
  ano?: number;
}

export interface FilterParams extends PeriodFilter {
  classificacao?: string;
  origem?: 'REAL' | 'ORC';
}

// Tipos para KPIs
export interface KPIItem {
  nome: string;
  valor: number;
  variacao?: number;
  formato: 'currency' | 'percentage' | 'number';
  trend?: 'up' | 'down' | 'stable';
}

export interface KPIsData {
  receita_liquida: KPIItem;
  lucro_bruto: KPIItem;
  lucro_operacional: KPIItem;
  lucro_liquido: KPIItem;
  margem_bruta: KPIItem;
  margem_operacional: KPIItem;
  margem_liquida: KPIItem;
  fluxo_operacional: KPIItem;
  fluxo_investimento: KPIItem;
  fluxo_financiamento: KPIItem;
  fluxo_livre: KPIItem;
}

// Tipos para análises
export interface AnaliseVertical {
  [conta: string]: {
    [periodo: string]: number; // percentual
  };
}

export interface AnaliseHorizontal {
  [conta: string]: {
    [periodo: string]: number; // variação percentual
  };
}

export interface RealizadoVsOrcado {
  [conta: string]: {
    real: number;
    orcado: number;
    variacao: number;
    variacao_percentual: number;
  };
}

// Tipos para upload de arquivos
export interface UploadResponse {
  success: boolean;
  message: string;
  filename?: string;
}

// Tipos para health check
export interface HealthResponse {
  status: 'healthy' | 'error';
  message: string;
  data_rows?: number;
  data_columns?: number;
  cache_status?: 'hit' | 'miss';
  cache_age?: number;
  response_time: number;
}

// Tipos para resposta de erro da API
export interface ApiError {
  error: string;
  details?: string;
}

// Tipo genérico para respostas da API
export type ApiResponse<T> = T | ApiError;

// Função type guard para verificar se é erro
export const isApiError = (response: any): response is ApiError => {
  return response && typeof response.error === 'string';
};
