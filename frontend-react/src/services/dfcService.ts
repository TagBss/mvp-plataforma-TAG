import { api, apiLongTimeout } from './api';
import type { 
  DFCData, 
  FilterParams, 
  ApiResponse, 
  KPIsData 
} from '../types/financial';
import { isApiError } from '../types/financial';

export class DFCService {
  private static readonly BASE_PATH = '/dfc';

  /**
   * Busca dados completos da DFC
   */
  static async getDFCData(filters?: FilterParams): Promise<DFCData> {
    try {
      const params = new URLSearchParams();
      
      if (filters?.mes) {
        params.append('mes', filters.mes);
      }
      if (filters?.classificacao) {
        params.append('classificacao', filters.classificacao);
      }
      if (filters?.origem) {
        params.append('origem', filters.origem);
      }

      const url = `${this.BASE_PATH}${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await apiLongTimeout.get<ApiResponse<DFCData>>(url);
      
      if (isApiError(response.data)) {
        throw new Error(response.data.error);
      }

      return response.data;
    } catch (error) {
      console.error('Erro ao buscar dados da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca dados da DFC para um mês específico
   */
  static async getDFCByMonth(mesAno: string): Promise<DFCData> {
    return this.getDFCData({ mes: mesAno });
  }

  /**
   * Busca dados da DFC para um ano específico
   */
  static async getDFCByYear(ano: number): Promise<DFCData> {
    return this.getDFCData({ ano });
  }

  /**
   * Busca apenas os totalizadores da DFC
   */
  static async getDFCTotalizadores(filters?: FilterParams): Promise<Record<string, number>> {
    try {
      const data = await this.getDFCData(filters);
      return data.totalizadores;
    } catch (error) {
      console.error('Erro ao buscar totalizadores da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca saldos inicial e final da DFC
   */
  static async getDFCSaldos(filters?: FilterParams): Promise<{
    saldo_inicial: Record<string, number>;
    saldo_final: Record<string, number>;
  }> {
    try {
      const data = await this.getDFCData(filters);
      return {
        saldo_inicial: data.saldo_inicial || {},
        saldo_final: data.saldo_final || {},
      };
    } catch (error) {
      console.error('Erro ao buscar saldos da DFC:', error);
      throw error;
    }
  }

  /**
   * Calcula KPIs de fluxo de caixa baseados nos dados da DFC
   */
  static async getDFCKPIs(filters?: FilterParams): Promise<Partial<KPIsData>> {
    try {
      const data = await this.getDFCData(filters);
      
      // Verificar se os dados existem
      if (!data || !data.total_geral_real) {
        console.warn('Dados da DFC não encontrados ou incompletos');
        return {
          fluxo_operacional: {
            nome: 'Fluxo Operacional',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          fluxo_investimento: {
            nome: 'Fluxo de Investimento',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          fluxo_financiamento: {
            nome: 'Fluxo de Financiamento',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          fluxo_livre: {
            nome: 'Fluxo de Caixa Livre',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
        };
      }
      
      // Mapear fluxos principais com verificação de segurança
      const fluxoOperacional = data.total_geral_real['Fluxo Operacional'] || 0;
      const fluxoInvestimento = data.total_geral_real['Fluxo de Investimento'] || 0;
      const fluxoFinanciamento = data.total_geral_real['Fluxo de Financiamento'] || 0;
      
      // Calcular fluxo de caixa livre
      const fluxoLivre = fluxoOperacional + fluxoInvestimento;

      return {
        fluxo_operacional: {
          nome: 'Fluxo Operacional',
          valor: fluxoOperacional,
          formato: 'currency',
          trend: fluxoOperacional > 0 ? 'up' : 'down',
        },
        fluxo_investimento: {
          nome: 'Fluxo de Investimento',
          valor: fluxoInvestimento,
          formato: 'currency',
          trend: fluxoInvestimento < 0 ? 'up' : 'down', // Investimento negativo é bom
        },
        fluxo_financiamento: {
          nome: 'Fluxo de Financiamento',
          valor: fluxoFinanciamento,
          formato: 'currency',
          trend: 'stable',
        },
        fluxo_livre: {
          nome: 'Fluxo de Caixa Livre',
          valor: fluxoLivre,
          formato: 'currency',
          trend: fluxoLivre > 0 ? 'up' : 'down',
        },
      };
    } catch (error) {
      console.error('Erro ao calcular KPIs da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca estrutura hierárquica da DFC
   */
  static async getDFCHierarchy(filters?: FilterParams): Promise<any[]> {
    try {
      const data = await this.getDFCData(filters);
      return data.estrutura_hierarquica || [];
    } catch (error) {
      console.error('Erro ao buscar hierarquia da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca análise vertical da DFC
   */
  static async getDFCAnaliseVertical(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDFCData(filters);
      return data.analise_vertical || {};
    } catch (error) {
      console.error('Erro ao buscar análise vertical da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca análise horizontal da DFC
   */
  static async getDFCAnaliseHorizontal(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDFCData(filters);
      return data.analise_horizontal || {};
    } catch (error) {
      console.error('Erro ao buscar análise horizontal da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca comparação realizado vs orçado da DFC
   */
  static async getDFCRealizadoVsOrcado(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDFCData(filters);
      return data.realizado_vs_orcado || {};
    } catch (error) {
      console.error('Erro ao buscar realizado vs orçado da DFC:', error);
      throw error;
    }
  }

  /**
   * Busca dados de movimentações por período
   */
  static async getDFCMovimentacoes(filters?: FilterParams): Promise<{
    por_mes: Record<string, Record<string, number>>;
    por_trimestre: Record<string, Record<string, number>>;
    por_ano: Record<number, Record<string, number>>;
  }> {
    try {
      const data = await this.getDFCData(filters);
      return {
        por_mes: data.total_real_por_mes || {},
        por_trimestre: data.total_real_por_tri || {},
        por_ano: data.total_real_por_ano || {},
      };
    } catch (error) {
      console.error('Erro ao buscar movimentações da DFC:', error);
      throw error;
    }
  }
}

export default DFCService;
