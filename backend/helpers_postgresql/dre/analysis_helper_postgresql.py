"""
Helper para análises financeiras PostgreSQL - versão independente da versão Excel
"""
import pandas as pd
from typing import Dict, Any

def calcular_analise_vertical_postgresql(valor: float, base: float) -> str:
    """Calcula análise vertical (percentual do total) para PostgreSQL"""
    try:
        if base == 0:
            return "–"
        percentual = (valor / base) * 100
        return f"{percentual:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_analise_horizontal_postgresql(valor_atual: float, valor_anterior: float) -> str:
    """Calcula análise horizontal (variação percentual) para PostgreSQL"""
    try:
        if valor_anterior == 0:
            return "–"
        variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
        return f"{variacao:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_realizado_vs_orcado_postgresql(realizado: float, orcado: float) -> str:
    """Calcula realizado vs orçado (percentual) para PostgreSQL"""
    try:
        if orcado == 0:
            return "–"
        percentual = (realizado / orcado) * 100
        return f"{percentual:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_analises_completas_postgresql(valores_mes: Dict[str, float], valores_tri: Dict[str, float], 
                                         valores_ano: Dict[str, float], valores_total: float,
                                         orcamentos_mes: Dict[str, float], orcamentos_tri: Dict[str, float], 
                                         orcamentos_ano: Dict[str, float], orcamento_total: float,
                                         meses_unicos: list, trimestres_unicos: list, anos_unicos: list, 
                                         base_vertical: float = None):
    """Calcula todas as análises financeiras para um item (PostgreSQL)"""
    
    def safe_real_vs_orcado(real, orcado):
        try:
            real_num = float(real) if real is not None else 0
            orcado_num = float(orcado) if orcado is not None else 0
            return calcular_realizado_vs_orcado_postgresql(real_num, orcado_num)
        except (ValueError, TypeError):
            return "–"
    
    def safe_vertical(valor, base):
        try:
            if base is None or base == 0:
                return "–"
            return calcular_analise_vertical_postgresql(valor, base)
        except (ValueError, TypeError, ZeroDivisionError):
            return "–"
    
    # Real vs Orçamento
    real_vs_orcamento_mensais = {mes: safe_real_vs_orcado(valores_mes[mes], orcamentos_mes[mes]) for mes in meses_unicos}
    real_vs_orcamento_trimestrais = {tri: safe_real_vs_orcado(valores_tri[tri], orcamentos_tri[tri]) for tri in trimestres_unicos}
    real_vs_orcamento_anuais = {str(ano): safe_real_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)]) for ano in anos_unicos}
    real_vs_orcamento_total = safe_real_vs_orcado(valores_total, orcamento_total)

    # Horizontal Realizado
    horizontal_mensais = {}
    for i, mes in enumerate(meses_unicos):
        if i == 0:
            horizontal_mensais[mes] = "–"
        else:
            horizontal_mensais[mes] = calcular_analise_horizontal_postgresql(valores_mes[mes], valores_mes[meses_unicos[i-1]])

    horizontal_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_trimestrais[tri] = "–"
        else:
            horizontal_trimestrais[tri] = calcular_analise_horizontal_postgresql(valores_tri[tri], valores_tri[trimestres_unicos[i-1]])

    horizontal_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_anuais[str(ano)] = "–"
        else:
            horizontal_anuais[str(ano)] = calcular_analise_horizontal_postgresql(valores_ano[str(ano)], valores_ano[str(anos_unicos[i-1])])

    # Vertical Realizado
    vertical_mensais = {}
    for mes in meses_unicos:
        vertical_mensais[mes] = safe_vertical(valores_mes[mes], base_vertical)

    vertical_trimestrais = {}
    for tri in trimestres_unicos:
        vertical_trimestrais[tri] = safe_vertical(valores_tri[tri], base_vertical)

    vertical_anuais = {}
    for ano in anos_unicos:
        vertical_anuais[str(ano)] = safe_vertical(valores_ano[str(ano)], base_vertical)

    vertical_total = safe_vertical(valores_total, base_vertical)

    # Vertical Orçamento
    vertical_orcamentos_mensais = {}
    for mes in meses_unicos:
        vertical_orcamentos_mensais[mes] = safe_vertical(orcamentos_mes[mes], base_vertical)

    vertical_orcamentos_trimestrais = {}
    for tri in trimestres_unicos:
        vertical_orcamentos_trimestrais[tri] = safe_vertical(orcamentos_tri[tri], base_vertical)

    vertical_orcamentos_anuais = {}
    for ano in anos_unicos:
        vertical_orcamentos_anuais[str(ano)] = safe_vertical(orcamentos_ano[str(ano)], base_vertical)

    vertical_orcamentos_total = safe_vertical(orcamento_total, base_vertical)

    # Horizontal Orçamento
    horizontal_orcamentos_mensais = {}
    for i, mes in enumerate(meses_unicos):
        if i == 0:
            horizontal_orcamentos_mensais[mes] = "–"
        else:
            horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal_postgresql(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i-1]])

    horizontal_orcamentos_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_orcamentos_trimestrais[tri] = "–"
        else:
            horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal_postgresql(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i-1]])

    horizontal_orcamentos_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_orcamentos_anuais[str(ano)] = "–"
        else:
            horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal_postgresql(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i-1])])

    return {
        # Realizado
        "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
        "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
        "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
        "real_vs_orcamento_total": real_vs_orcamento_total,
        
        # Horizontal Realizado
        "horizontal_mensais": horizontal_mensais,
        "horizontal_trimestrais": horizontal_trimestrais,
        "horizontal_anuais": horizontal_anuais,
        
        # Vertical Realizado
        "vertical_mensais": vertical_mensais,
        "vertical_trimestrais": vertical_trimestrais,
        "vertical_anuais": vertical_anuais,
        "vertical_total": vertical_total,
        
        # Vertical Orçamento
        "vertical_orcamentos_mensais": vertical_orcamentos_mensais,
        "vertical_orcamentos_trimestrais": vertical_orcamentos_trimestrais,
        "vertical_orcamentos_anuais": vertical_orcamentos_anuais,
        "vertical_orcamentos_total": vertical_orcamentos_total,
        
        # Horizontal Orçamento
        "horizontal_orcamentos_mensais": horizontal_orcamentos_mensais,
        "horizontal_orcamentos_trimestrais": horizontal_orcamentos_trimestrais,
        "horizontal_orcamentos_anuais": horizontal_orcamentos_anuais
    }

def calcular_analises_horizontais_movimentacoes_postgresql(valores_mensais: Dict[str, float], 
                                                         valores_trimestrais: Dict[str, float], 
                                                         valores_anuais: Dict[str, float], 
                                                         meses_unicos: list, trimestres_unicos: list, 
                                                         anos_unicos: list):
    """Calcula análises horizontais para movimentações (PostgreSQL)"""
    
    horizontal_mensais = {}
    for i, mes in enumerate(meses_unicos):
        if i == 0:
            horizontal_mensais[mes] = "–"
        else:
            horizontal_mensais[mes] = calcular_analise_horizontal_postgresql(valores_mensais[mes], valores_mensais[meses_unicos[i-1]])

    horizontal_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_trimestrais[tri] = "–"
        else:
            horizontal_trimestrais[tri] = calcular_analise_horizontal_postgresql(valores_trimestrais[tri], valores_trimestrais[trimestres_unicos[i-1]])

    horizontal_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_anuais[str(ano)] = "–"
        else:
            horizontal_anuais[str(ano)] = calcular_analise_horizontal_postgresql(valores_anuais[str(ano)], valores_anuais[str(anos_unicos[i-1])])

    return {
        "horizontal_mensais": horizontal_mensais,
        "horizontal_trimestrais": horizontal_trimestrais,
        "horizontal_anuais": horizontal_anuais
    }
