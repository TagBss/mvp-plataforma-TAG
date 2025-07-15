// Utilitários compartilhados para cálculos financeiros

export interface FinancialItem {
  valores?: Record<string, number>
  orcamentos?: Record<string, number>
  analise_vertical?: Record<string, number>
  analise_horizontal?: Record<string, number>
  av_orcamento?: Record<string, number>
  ah_orcamento?: Record<string, number>
}

// Cálculos básicos
export const calcularValor = (item: FinancialItem, periodoLabel: string): number => {
  return item.valores?.[periodoLabel] ?? 0
}

export const calcularOrcamento = (item: FinancialItem, periodoLabel: string): number => {
  return item.orcamentos?.[periodoLabel] ?? 0
}

export const calcularTotal = (valores: Record<string, number> | undefined): number => {
  return valores ? Object.values(valores).reduce((acc, val) => acc + val, 0) : 0
}

export const calcularTotalOrcamento = (orcamentos: Record<string, number> | undefined): number => {
  return orcamentos ? Object.values(orcamentos).reduce((acc, val) => acc + val, 0) : 0
}

export const calcularDiffPct = (real: number, orcado: number): string | undefined => {
  if (orcado === 0) return undefined
  const diff = ((real - orcado) / orcado) * 100
  return `${diff > 0 ? '+' : ''}${diff.toFixed(1)}%`
}

// Função para formatar valores com cor vermelha para negativos
export const formatarValor = (valor: number, decimals: number = 0): string => {
  if (valor === 0) return '0'
  return valor.toLocaleString('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

export const formatarPorcentagem = (valor: string | undefined): string => {
  if (!valor || valor === '0.0%') return ''
  return valor
}

// Função para calcular análise vertical dinâmica
export const calcularVerticalTotalDinamica = (
  dados: FinancialItem[], 
  periodos: string[]
): number => {
  return dados.reduce((acc, item) => {
    const totalItem = calcularTotal(
      Object.fromEntries(
        periodos.map(p => [p, calcularValor(item, p)])
      )
    )
    return acc + totalItem
  }, 0)
}

// Função para calcular AV% dinâmica
export const calcularAVTotalDinamica = (
  valorTotal: number,
  dados: FinancialItem[],
  periodos: string[]
): string | undefined => {
  const totalGeral = calcularVerticalTotalDinamica(dados, periodos)
  if (totalGeral === 0) return undefined
  const av = (valorTotal / totalGeral) * 100
  return `${av.toFixed(1)}%`
}

// Função para renderizar valor da diferença
export const renderValorDiferenca = (real: number, orcado: number) => {
  const diferenca = real - orcado
  const diffPct = calcularDiffPct(real, orcado)
  
  return {
    valor: diferenca,
    porcentagem: diffPct,
    isNegativo: diferenca < 0
  }
}

// Função para renderizar valor com formatação
export const renderValorFormatado = (
  valor: number,
  av: string | undefined,
  ah: string | undefined,
  decimals: number = 0
) => {
  const valorFormatado = formatarValor(valor, decimals)
  const avFormatado = formatarPorcentagem(av)
  const ahFormatado = formatarPorcentagem(ah)
  
  return {
    valor: valorFormatado,
    av: avFormatado,
    ah: ahFormatado,
    isNegativo: valor < 0
  }
}
