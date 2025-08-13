"""
Utilitários financeiros para os helpers originais (versão Excel)
"""
import pandas as pd

def calcular_analise_vertical(valor, base):
    """Calcula análise vertical (percentual do total)"""
    try:
        if base == 0:
            return "–"
        percentual = (valor / base) * 100
        return f"{percentual:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_analise_horizontal(valor_atual, valor_anterior):
    """Calcula análise horizontal (variação percentual)"""
    try:
        if valor_anterior == 0:
            return "–"
        variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
        return f"{variacao:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_realizado_vs_orcado(realizado, orcado):
    """Calcula realizado vs orçado (percentual)"""
    try:
        if orcado == 0:
            return "–"
        percentual = (realizado / orcado) * 100
        return f"{percentual:.2f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "–"

def calcular_totalizadores(valores_dict, estrutura):
    """Calcula totalizadores dinamicamente baseados na estrutura"""
    totalizadores = {}
    
    for item in estrutura:
        totalizador_nome = item.get("totalizador")
        if totalizador_nome and totalizador_nome not in totalizadores:
            totalizadores[totalizador_nome] = 0
        
        if totalizador_nome:
            valor_conta = valores_dict.get(item["nome"], 0)
            if item["tipo"] in ["+", "+/-"]:
                totalizadores[totalizador_nome] += valor_conta
            elif item["tipo"] == "-":
                totalizadores[totalizador_nome] -= valor_conta
    
    return totalizadores
