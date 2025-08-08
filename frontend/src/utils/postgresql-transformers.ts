import { FinancialDataItem, FinancialSummary } from '../types/financial';

// Transformar dados PostgreSQL em formato DRE
export const transformToDREData = (data: FinancialDataItem[]) => {
  const dreData = {
    meses_unicos: [] as string[],
    anos_unicos: [] as number[],
    trimestres_unicos: [] as string[],
    total_real_por_mes: {} as Record<string, Record<string, number>>,
    total_orc_por_mes: {} as Record<string, Record<string, number>>,
    total_real_por_tri: {} as Record<string, Record<string, number>>,
    total_orc_por_tri: {} as Record<string, Record<string, number>>,
    total_real_por_ano: {} as Record<number, Record<string, number>>,
    total_orc_por_ano: {} as Record<number, Record<string, number>>,
    total_geral_real: {} as Record<string, number>,
    total_geral_orc: {} as Record<string, number>,
    contas_dre: [] as Array<[string, string]>,
    estrutura_hierarquica: [] as any[],
    analise_vertical: {} as Record<string, Record<string, number>>,
    analise_horizontal: {} as Record<string, Record<string, number>>,
    realizado_vs_orcado: {} as Record<string, Record<string, number>>,
    totalizadores: {} as Record<string, number>
  };

  // Agrupar dados por período
  data.forEach(item => {
    const date = new Date(item.date);
    const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const year = date.getFullYear();
    const quarter = `${date.getFullYear()}-T${Math.ceil((date.getMonth() + 1) / 3)}`;
    
    // Adicionar períodos únicos
    if (!dreData.meses_unicos.includes(month)) {
      dreData.meses_unicos.push(month);
    }
    if (!dreData.anos_unicos.includes(year)) {
      dreData.anos_unicos.push(year);
    }
    if (!dreData.trimestres_unicos.includes(quarter)) {
      dreData.trimestres_unicos.push(quarter);
    }

    // Agrupar por categoria e período
    const category = item.category;
    const value = item.value;
    const isBudget = item.is_budget;

    // Por mês
    if (!dreData.total_real_por_mes[month]) {
      dreData.total_real_por_mes[month] = {};
    }
    if (!dreData.total_orc_por_mes[month]) {
      dreData.total_orc_por_mes[month] = {};
    }

    if (isBudget) {
      dreData.total_orc_por_mes[month][category] = (dreData.total_orc_por_mes[month][category] || 0) + value;
    } else {
      dreData.total_real_por_mes[month][category] = (dreData.total_real_por_mes[month][category] || 0) + value;
    }

    // Por trimestre
    if (!dreData.total_real_por_tri[quarter]) {
      dreData.total_real_por_tri[quarter] = {};
    }
    if (!dreData.total_orc_por_tri[quarter]) {
      dreData.total_orc_por_tri[quarter] = {};
    }

    if (isBudget) {
      dreData.total_orc_por_tri[quarter][category] = (dreData.total_orc_por_tri[quarter][category] || 0) + value;
    } else {
      dreData.total_real_por_tri[quarter][category] = (dreData.total_real_por_tri[quarter][category] || 0) + value;
    }

    // Por ano
    if (!dreData.total_real_por_ano[year]) {
      dreData.total_real_por_ano[year] = {};
    }
    if (!dreData.total_orc_por_ano[year]) {
      dreData.total_orc_por_ano[year] = {};
    }

    if (isBudget) {
      dreData.total_orc_por_ano[year][category] = (dreData.total_orc_por_ano[year][category] || 0) + value;
    } else {
      dreData.total_real_por_ano[year][category] = (dreData.total_real_por_ano[year][category] || 0) + value;
    }

    // Totalizadores
    if (isBudget) {
      dreData.total_geral_orc[category] = (dreData.total_geral_orc[category] || 0) + value;
    } else {
      dreData.total_geral_real[category] = (dreData.total_geral_real[category] || 0) + value;
    }
  });

  // Ordenar períodos
  dreData.meses_unicos.sort();
  dreData.anos_unicos.sort();
  dreData.trimestres_unicos.sort();

  // Criar contas DRE baseadas nas categorias
  const uniqueCategories = [...new Set(data.map(item => item.category))];
  dreData.contas_dre = uniqueCategories.map(category => {
    // Encontrar um item com essa categoria para determinar o tipo
    const itemWithCategory = data.find(item => item.category === category);
    return [category, itemWithCategory?.type === 'receita' ? '+' : '-'];
  });

  return dreData;
};

// Transformar dados PostgreSQL em formato DFC
export const transformToDFCData = (data: FinancialDataItem[]) => {
  const dfcData = {
    meses_unicos: [] as string[],
    anos_unicos: [] as number[],
    trimestres_unicos: [] as string[],
    total_real_por_mes: {} as Record<string, Record<string, number>>,
    total_orc_por_mes: {} as Record<string, Record<string, number>>,
    total_real_por_tri: {} as Record<string, Record<string, number>>,
    total_orc_por_tri: {} as Record<string, Record<string, number>>,
    total_real_por_ano: {} as Record<number, Record<string, number>>,
    total_orc_por_ano: {} as Record<number, Record<string, number>>,
    total_geral_real: {} as Record<string, number>,
    total_geral_orc: {} as Record<string, number>,
    contas_dfc: [] as Array<[string, string]>,
    estrutura_hierarquica: [] as any[],
    analise_vertical: {} as Record<string, Record<string, number>>,
    analise_horizontal: {} as Record<string, Record<string, number>>,
    realizado_vs_orcado: {} as Record<string, Record<string, number>>,
    totalizadores: {} as Record<string, number>,
    saldo_inicial: {} as Record<string, number>,
    saldo_final: {} as Record<string, number>
  };

  // Similar ao DRE, mas com foco em fluxo de caixa
  data.forEach(item => {
    const date = new Date(item.date);
    const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const year = date.getFullYear();
    const quarter = `${date.getFullYear()}-T${Math.ceil((date.getMonth() + 1) / 3)}`;
    
    // Adicionar períodos únicos
    if (!dfcData.meses_unicos.includes(month)) {
      dfcData.meses_unicos.push(month);
    }
    if (!dfcData.anos_unicos.includes(year)) {
      dfcData.anos_unicos.push(year);
    }
    if (!dfcData.trimestres_unicos.includes(quarter)) {
      dfcData.trimestres_unicos.push(quarter);
    }

    // Agrupar por categoria e período
    const category = item.category;
    const value = item.value;
    const isBudget = item.is_budget;

    // Por mês
    if (!dfcData.total_real_por_mes[month]) {
      dfcData.total_real_por_mes[month] = {};
    }
    if (!dfcData.total_orc_por_mes[month]) {
      dfcData.total_orc_por_mes[month] = {};
    }

    if (isBudget) {
      dfcData.total_orc_por_mes[month][category] = (dfcData.total_orc_por_mes[month][category] || 0) + value;
    } else {
      dfcData.total_real_por_mes[month][category] = (dfcData.total_real_por_mes[month][category] || 0) + value;
    }

    // Por trimestre
    if (!dfcData.total_real_por_tri[quarter]) {
      dfcData.total_real_por_tri[quarter] = {};
    }
    if (!dfcData.total_orc_por_tri[quarter]) {
      dfcData.total_orc_por_tri[quarter] = {};
    }

    if (isBudget) {
      dfcData.total_orc_por_tri[quarter][category] = (dfcData.total_orc_por_tri[quarter][category] || 0) + value;
    } else {
      dfcData.total_real_por_tri[quarter][category] = (dfcData.total_real_por_tri[quarter][category] || 0) + value;
    }

    // Por ano
    if (!dfcData.total_real_por_ano[year]) {
      dfcData.total_real_por_ano[year] = {};
    }
    if (!dfcData.total_orc_por_ano[year]) {
      dfcData.total_orc_por_ano[year] = {};
    }

    if (isBudget) {
      dfcData.total_orc_por_ano[year][category] = (dfcData.total_orc_por_ano[year][category] || 0) + value;
    } else {
      dfcData.total_real_por_ano[year][category] = (dfcData.total_real_por_ano[year][category] || 0) + value;
    }

    // Totalizadores
    if (isBudget) {
      dfcData.total_geral_orc[category] = (dfcData.total_geral_orc[category] || 0) + value;
    } else {
      dfcData.total_geral_real[category] = (dfcData.total_geral_real[category] || 0) + value;
    }
  });

  // Ordenar períodos
  dfcData.meses_unicos.sort();
  dfcData.anos_unicos.sort();
  dfcData.trimestres_unicos.sort();

  // Criar contas DFC baseadas nas categorias
  const uniqueCategories = [...new Set(data.map(item => item.category))];
  dfcData.contas_dfc = uniqueCategories.map(category => {
    // Encontrar um item com essa categoria para determinar o tipo
    const itemWithCategory = data.find(item => item.category === category);
    return [category, itemWithCategory?.type === 'receita' ? '+' : '-'];
  });

  return dfcData;
};

// Transformar dados PostgreSQL em KPIs
export const transformToKPIs = (data: FinancialDataItem[], summary: FinancialSummary) => {
  const kpis = {
    receita_liquida: { nome: 'Receita Líquida', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const },
    lucro_bruto: { nome: 'Lucro Bruto', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const },
    lucro_operacional: { nome: 'Lucro Operacional', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const },
    lucro_liquido: { nome: 'Lucro Líquido', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const },
    margem_bruta: { nome: 'Margem Bruta', valor: 0, variacao: 0, formato: 'percentage' as const, trend: 'up' as const },
    margem_operacional: { nome: 'Margem Operacional', valor: 0, variacao: 0, formato: 'percentage' as const, trend: 'up' as const },
    margem_liquida: { nome: 'Margem Líquida', valor: 0, variacao: 0, formato: 'percentage' as const, trend: 'up' as const },
    fluxo_operacional: { nome: 'Fluxo Operacional', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const },
    fluxo_investimento: { nome: 'Fluxo de Investimento', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'down' as const },
    fluxo_financiamento: { nome: 'Fluxo de Financiamento', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'stable' as const },
    fluxo_livre: { nome: 'Fluxo Livre', valor: 0, variacao: 0, formato: 'currency' as const, trend: 'up' as const }
  };

  // Calcular KPIs baseados no summary
  if (summary && summary.summary) {
    const receita = summary.summary.receita || 0;
    const despesa = summary.summary.despesa || 0;
    const investimento = summary.summary.investimento || 0;

    kpis.receita_liquida.valor = receita;
    kpis.lucro_bruto.valor = receita - despesa;
    kpis.lucro_operacional.valor = receita - despesa;
    kpis.lucro_liquido.valor = receita - despesa - investimento;
    kpis.fluxo_operacional.valor = receita - despesa;
    kpis.fluxo_investimento.valor = -investimento;
    kpis.fluxo_financiamento.valor = 0; // Placeholder
    kpis.fluxo_livre.valor = receita - despesa - investimento;

    // Calcular margens
    if (receita > 0) {
      kpis.margem_bruta.valor = ((receita - despesa) / receita) * 100;
      kpis.margem_operacional.valor = ((receita - despesa) / receita) * 100;
      kpis.margem_liquida.valor = ((receita - despesa - investimento) / receita) * 100;
    }
  }

  return kpis;
};

// Função helper para agrupar dados por período
export const groupDataByPeriod = (data: FinancialDataItem[], periodType: 'month' | 'quarter' | 'year') => {
  const grouped: Record<string, Record<string, number>> = {};

  data.forEach(item => {
    const date = new Date(item.date);
    let period: string;

    switch (periodType) {
      case 'month':
        period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        break;
      case 'quarter':
        period = `${date.getFullYear()}-T${Math.ceil((date.getMonth() + 1) / 3)}`;
        break;
      case 'year':
        period = date.getFullYear().toString();
        break;
    }

    if (!grouped[period]) {
      grouped[period] = {};
    }

    const category = item.category;
    grouped[period][category] = (grouped[period][category] || 0) + item.value;
  });

  return grouped;
};

// Função helper para calcular totais por categoria
export const calculateTotalsByCategory = (data: FinancialDataItem[]) => {
  const totals: Record<string, number> = {};

  data.forEach(item => {
    const category = item.category;
    totals[category] = (totals[category] || 0) + item.value;
  });

  return totals;
};
