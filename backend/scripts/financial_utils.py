"""
Funções utilitárias para cálculos financeiros no backend
"""
import math
from typing import Dict, Any, Union

def calcular_analise_vertical(valor: float, base_valor: float) -> str:
    """Função única para análise vertical"""
    if base_valor is None or base_valor == 0 or math.isnan(base_valor):
        return "–"
    return f"{((valor / base_valor) * 100):.1f}%"

def calcular_analise_horizontal(valor_atual: float, valor_anterior: float) -> str:
    """Função para análise horizontal"""
    if valor_anterior is None or valor_anterior == 0 or math.isnan(valor_anterior):
        return "–"
    diff = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return f"{diff:+.1f}%"

def calcular_realizado_vs_orcado(real: float, orcado: float) -> str:
    """Função para calcular real vs orçado"""
    if orcado is None or orcado == 0 or math.isnan(orcado):
        return "–"
    diff = ((real - orcado) / orcado) * 100
    return f"{diff:+.1f}%"

def calcular_totalizadores(valores_dict: Dict[str, float]) -> float:
    """Calcula total de um dicionário de valores"""
    return sum(v for v in valores_dict.values() if v is not None and not math.isnan(v))

def processar_periodos_financeiros(df, date_column: str):
    """Processa e retorna períodos únicos dos dados"""
    df[date_column] = df[date_column].dt.to_datetime(errors="coerce")
    df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
    df["ano"] = df[date_column].dt.year
    df["trimestre"] = df[date_column].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")
    
    meses_unicos = sorted(df["mes_ano"].dropna().unique())
    anos_unicos = sorted(set(int(a) for a in df["ano"].dropna().unique()))
    trimestres_unicos = sorted(df["trimestre"].dropna().unique())
    
    return meses_unicos, anos_unicos, trimestres_unicos

def calcular_valores_por_periodo(df, group_column: str, value_column: str, period_column: str, periods: list):
    """Calcula valores agrupados por período"""
    return {
        periodo: df[df[period_column] == periodo].groupby(group_column)[value_column].sum().to_dict()
        for periodo in periods
    }

def agregar_por_periodo_superior(valores_por_periodo_base: Dict, mapeamento_periodos: Dict, periodos_superiores: list):
    """Agrega valores de períodos menores para períodos maiores (ex: meses -> trimestres)"""
    resultado = {}
    for periodo_superior in periodos_superiores:
        periodos_base = mapeamento_periodos.get(periodo_superior, [])
        soma = {}
        for periodo_base in periodos_base:
            for k, v in valores_por_periodo_base.get(periodo_base, {}).items():
                soma[k] = soma.get(k, 0) + v
        resultado[periodo_superior] = soma
    return resultado

def calcular_analises_completas(valores: Dict[str, float], valores_base: Dict[str, float], 
                              valores_anteriores: Dict[str, float], orcamentos: Dict[str, float]):
    """Calcula análises vertical, horizontal e vs orçado para um conjunto de valores"""
    analise_vertical = {}
    analise_horizontal = {}
    realizado_vs_orcado = {}
    
    for key, valor in valores.items():
        # Análise vertical
        base_valor = valores_base.get(key, 0)
        analise_vertical[key] = calcular_analise_vertical(valor, base_valor)
        
        # Análise horizontal
        valor_anterior = valores_anteriores.get(key, 0)
        analise_horizontal[key] = calcular_analise_horizontal(valor, valor_anterior)
        
        # Realizado vs orçado
        orcado = orcamentos.get(key, 0)
        realizado_vs_orcado[key] = calcular_realizado_vs_orcado(valor, orcado)
    
    return analise_vertical, analise_horizontal, realizado_vs_orcado

def formatar_item_financeiro(nome: str, valores_dict: Dict, orcamentos_dict: Dict,
                           analise_vertical: Dict, analise_horizontal: Dict,
                           av_orcamento: Dict, ah_orcamento: Dict, 
                           realizado_vs_orcado: Dict, classificacoes: list = None):
    """Formata um item financeiro com todos os cálculos"""
    return {
        "nome": nome,
        "valores": valores_dict,
        "orcamentos": orcamentos_dict,
        "analise_vertical": analise_vertical,
        "analise_horizontal": analise_horizontal,
        "av_orcamento": av_orcamento,
        "ah_orcamento": ah_orcamento,
        "realizado_vs_orcado": realizado_vs_orcado,
        "classificacoes": classificacoes or []
    }
