import { DREService } from './dreService';
import { DFCService } from './dfcService';
import { checkHealth } from './api';
import type { 
  FilterParams, 
  KPIsData, 
  HealthResponse,
  DREData,
  DFCData 
} from '../types/financial';

export class FinancialService {
  /**
   * Busca KPIs completos combinando DRE e DFC
   */
  static async getKPIsCompletos(filters?: FilterParams): Promise<KPIsData> {
    try {
      const [dreKPIs, dfcKPIs] = await Promise.all([
        DREService.getDREKPIs(filters),
        DFCService.getDFCKPIs(filters),
      ]);

      return {
        ...dreKPIs,
        ...dfcKPIs,
      };
    } catch (error) {
      console.error('Erro ao buscar KPIs completos:', error);
      throw error;
    }
  }

  /**
   * Busca dados financeiros completos (DRE + DFC)
   */
  static async getDadosCompletos(filters?: FilterParams): Promise<{
    dre: DREData;
    dfc: DFCData;
  }> {
    try {
      const [dreData, dfcData] = await Promise.all([
        DREService.getDREData(filters),
        DFCService.getDFCData(filters),
      ]);

      return {
        dre: dreData,
        dfc: dfcData,
      };
    } catch (error) {
      console.error('Erro ao buscar dados completos:', error);
      throw error;
    }
  }

  /**
   * Busca períodos disponíveis nos dados
   */
  static async getPeriodosDisponiveis(): Promise<{
    meses: string[];
    anos: number[];
    trimestres: string[];
  }> {
    try {
      // Usar DRE como base para períodos disponíveis
      const dreData = await DREService.getDREData();
      
      return {
        meses: dreData.meses_unicos || [],
        anos: dreData.anos_unicos || [],
        trimestres: dreData.trimestres_unicos || [],
      };
    } catch (error) {
      console.error('Erro ao buscar períodos disponíveis:', error);
      throw error;
    }
  }

  /**
   * Busca dados para dashboard principal
   */
  static async getDadosDashboard(filters?: FilterParams): Promise<{
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
  }> {
    try {
      const [kpis, periodos] = await Promise.all([
        this.getKPIsCompletos(filters),
        this.getPeriodosDisponiveis(),
      ]);

      const resumo = {
        receita_total: kpis.receita_liquida?.valor || 0,
        lucro_total: kpis.lucro_liquido?.valor || 0,
        fluxo_operacional: kpis.fluxo_operacional?.valor || 0,
        margem_liquida: kpis.margem_liquida?.valor || 0,
      };

      return {
        kpis,
        periodos,
        resumo,
      };
    } catch (error) {
      console.error('Erro ao buscar dados do dashboard:', error);
      throw error;
    }
  }

  /**
   * Busca dados para análise comparativa entre períodos
   */
  static async getAnaliseComparativa(periodo1: FilterParams, periodo2: FilterParams): Promise<{
    periodo1: {
      dre: DREData;
      dfc: DFCData;
      kpis: KPIsData;
    };
    periodo2: {
      dre: DREData;
      dfc: DFCData;
      kpis: KPIsData;
    };
    comparacao: {
      receita_variacao: number;
      lucro_variacao: number;
      fluxo_variacao: number;
      margem_variacao: number;
    };
  }> {
    try {
      const [dados1, dados2] = await Promise.all([
        this.getDadosCompletos(periodo1),
        this.getDadosCompletos(periodo2),
      ]);

      const [kpis1, kpis2] = await Promise.all([
        this.getKPIsCompletos(periodo1),
        this.getKPIsCompletos(periodo2),
      ]);

      // Calcular variações
      const receita1 = kpis1.receita_liquida?.valor || 0;
      const receita2 = kpis2.receita_liquida?.valor || 0;
      const lucro1 = kpis1.lucro_liquido?.valor || 0;
      const lucro2 = kpis2.lucro_liquido?.valor || 0;
      const fluxo1 = kpis1.fluxo_operacional?.valor || 0;
      const fluxo2 = kpis2.fluxo_operacional?.valor || 0;
      const margem1 = kpis1.margem_liquida?.valor || 0;
      const margem2 = kpis2.margem_liquida?.valor || 0;

      const comparacao = {
        receita_variacao: receita1 !== 0 ? ((receita2 - receita1) / receita1) * 100 : 0,
        lucro_variacao: lucro1 !== 0 ? ((lucro2 - lucro1) / lucro1) * 100 : 0,
        fluxo_variacao: fluxo1 !== 0 ? ((fluxo2 - fluxo1) / fluxo1) * 100 : 0,
        margem_variacao: margem2 - margem1, // Diferença absoluta para margem
      };

      return {
        periodo1: {
          dre: dados1.dre,
          dfc: dados1.dfc,
          kpis: kpis1,
        },
        periodo2: {
          dre: dados2.dre,
          dfc: dados2.dfc,
          kpis: kpis2,
        },
        comparacao,
      };
    } catch (error) {
      console.error('Erro ao buscar análise comparativa:', error);
      throw error;
    }
  }

  /**
   * Verifica se a API está funcionando
   */
  static async verificarSaude(): Promise<HealthResponse> {
    try {
      return await checkHealth();
    } catch (error) {
      console.error('Erro ao verificar saúde da API:', error);
      throw error;
    }
  }

  /**
   * Busca dados para gráficos de tendência
   */
  static async getDadosTendencia(conta: string, tipo: 'dre' | 'dfc'): Promise<{
    meses: string[];
    valores_real: number[];
    valores_orc: number[];
  }> {
    try {
      const data = tipo === 'dre' 
        ? await DREService.getDREData()
        : await DFCService.getDFCData();

      const meses = data.meses_unicos || [];
      const valoresReal: number[] = [];
      const valoresOrc: number[] = [];

      meses.forEach(mes => {
        const realPorMes = data.total_real_por_mes[mes] || {};
        const orcPorMes = data.total_orc_por_mes[mes] || {};
        
        valoresReal.push(realPorMes[conta] || 0);
        valoresOrc.push(orcPorMes[conta] || 0);
      });

      return {
        meses,
        valores_real: valoresReal,
        valores_orc: valoresOrc,
      };
    } catch (error) {
      console.error('Erro ao buscar dados de tendência:', error);
      throw error;
    }
  }
}

// Exportar também os serviços individuais
export { DREService } from './dreService';
export { DFCService } from './dfcService';
export { api, checkHealth } from './api';

export default FinancialService;
