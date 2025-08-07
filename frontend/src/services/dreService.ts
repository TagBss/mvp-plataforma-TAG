import { api, apiLongTimeout } from './api';
import type { 
  DREData, 
  FilterParams, 
  ApiResponse, 
  KPIsData 
} from '../types/financial';
import { isApiError } from '../types/financial';

export class DREService {
  private static readonly BASE_PATH = '/dre';

  /**
   * Busca dados completos da DRE
   */
  static async getDREData(filters?: FilterParams): Promise<DREData> {
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
      const response = await apiLongTimeout.get<ApiResponse<DREData>>(url);
      
      if (isApiError(response.data)) {
        throw new Error(response.data.error);
      }

      return response.data;
    } catch (error) {
      console.error('Erro ao buscar dados da DRE:', error);
      throw error;
    }
  }

  /**
   * Busca dados da DRE para um mês específico
   */
  static async getDREByMonth(mesAno: string): Promise<DREData> {
    return this.getDREData({ mes: mesAno });
  }

  /**
   * Busca dados da DRE para um ano específico
   */
  static async getDREByYear(ano: number): Promise<DREData> {
    return this.getDREData({ ano });
  }

  /**
   * Busca apenas os totalizadores da DRE
   */
  static async getDRETotalizadores(filters?: FilterParams): Promise<Record<string, number>> {
    try {
      const data = await this.getDREData(filters);
      return data.totalizadores;
    } catch (error) {
      console.error('Erro ao buscar totalizadores da DRE:', error);
      throw error;
    }
  }

  /**
   * Calcula KPIs baseados nos dados da DRE
   */
  static async getDREKPIs(filters?: FilterParams): Promise<KPIsData> {
    try {
      const data = await this.getDREData(filters);
      
      // Verificar se os dados existem
      if (!data || !data.total_geral_real) {
        console.warn('Dados da DRE não encontrados ou incompletos');
        return {
          receita_liquida: {
            nome: 'Receita Líquida',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          lucro_bruto: {
            nome: 'Lucro Bruto',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          lucro_operacional: {
            nome: 'Lucro Operacional',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          lucro_liquido: {
            nome: 'Lucro Líquido',
            valor: 0,
            formato: 'currency',
            trend: 'stable',
          },
          margem_bruta: {
            nome: 'Margem Bruta',
            valor: 0,
            formato: 'percentage',
            trend: 'stable',
          },
          margem_operacional: {
            nome: 'Margem Operacional',
            valor: 0,
            formato: 'percentage',
            trend: 'stable',
          },
          margem_liquida: {
            nome: 'Margem Líquida',
            valor: 0,
            formato: 'percentage',
            trend: 'stable',
          },
          // Placeholder para KPIs de fluxo de caixa (vindos do DFC)
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
      
      // Mapear contas principais
      const receita = data.total_geral_real['Receita Líquida'] || 0;
      const custos = data.total_geral_real['Custos'] || 0;
      const despesas = data.total_geral_real['Despesas Operacionais'] || 0;
      const lucroLiquido = data.total_geral_real['Lucro Líquido'] || 0;
      
      const lucroBruto = receita - custos;
      const lucroOperacional = lucroBruto - despesas;
      
      // Calcular margens
      const margemBruta = receita > 0 ? (lucroBruto / receita) * 100 : 0;
      const margemOperacional = receita > 0 ? (lucroOperacional / receita) * 100 : 0;
      const margemLiquida = receita > 0 ? (lucroLiquido / receita) * 100 : 0;

      return {
        receita_liquida: {
          nome: 'Receita Líquida',
          valor: receita,
          formato: 'currency',
          trend: receita > 0 ? 'up' : 'down',
        },
        lucro_bruto: {
          nome: 'Lucro Bruto',
          valor: lucroBruto,
          formato: 'currency',
          trend: lucroBruto > 0 ? 'up' : 'down',
        },
        lucro_operacional: {
          nome: 'Lucro Operacional',
          valor: lucroOperacional,
          formato: 'currency',
          trend: lucroOperacional > 0 ? 'up' : 'down',
        },
        lucro_liquido: {
          nome: 'Lucro Líquido',
          valor: lucroLiquido,
          formato: 'currency',
          trend: lucroLiquido > 0 ? 'up' : 'down',
        },
        margem_bruta: {
          nome: 'Margem Bruta',
          valor: margemBruta,
          formato: 'percentage',
          trend: margemBruta > 0 ? 'up' : 'down',
        },
        margem_operacional: {
          nome: 'Margem Operacional',
          valor: margemOperacional,
          formato: 'percentage',
          trend: margemOperacional > 0 ? 'up' : 'down',
        },
        margem_liquida: {
          nome: 'Margem Líquida',
          valor: margemLiquida,
          formato: 'percentage',
          trend: margemLiquida > 0 ? 'up' : 'down',
        },
        // Placeholder para KPIs de fluxo de caixa (vindos do DFC)
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
    } catch (error) {
      console.error('Erro ao calcular KPIs da DRE:', error);
      throw error;
    }
  }

  /**
   * Busca estrutura hierárquica da DRE
   */
  static async getDREHierarchy(filters?: FilterParams): Promise<any[]> {
    try {
      const data = await this.getDREData(filters);
      return data.estrutura_hierarquica || [];
    } catch (error) {
      console.error('Erro ao buscar hierarquia da DRE:', error);
      throw error;
    }
  }

  /**
   * Busca análise vertical da DRE
   */
  static async getDREAnaliseVertical(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDREData(filters);
      return data.analise_vertical || {};
    } catch (error) {
      console.error('Erro ao buscar análise vertical da DRE:', error);
      throw error;
    }
  }

  /**
   * Busca análise horizontal da DRE
   */
  static async getDREAnaliseHorizontal(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDREData(filters);
      return data.analise_horizontal || {};
    } catch (error) {
      console.error('Erro ao buscar análise horizontal da DRE:', error);
      throw error;
    }
  }

  /**
   * Busca comparação realizado vs orçado da DRE
   */
  static async getDRERealizadoVsOrcado(filters?: FilterParams): Promise<Record<string, Record<string, number>>> {
    try {
      const data = await this.getDREData(filters);
      return data.realizado_vs_orcado || {};
    } catch (error) {
      console.error('Erro ao buscar realizado vs orçado da DRE:', error);
      throw error;
    }
  }
}

export default DREService;
