"""
Helper para processamento de dados PostgreSQL - versão independente da versão Excel
"""
import pandas as pd
from datetime import date, datetime
from typing import List, Dict, Any

def processar_dados_financeiros_postgresql(df: pd.DataFrame, date_column: str, valor_column: str = "value"):
    """Processa dados financeiros básicos para PostgreSQL"""
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df["mes"] = df[date_column].dt.strftime('%Y-%m')
    df["ano"] = df[date_column].dt.year
    df["trimestre"] = df[date_column].dt.to_period('Q').astype(str)

    df[valor_column] = pd.to_numeric(df[valor_column], errors="coerce")
    df = df.dropna(subset=[date_column, valor_column])

    meses_unicos = sorted(df["mes"].dropna().unique())
    anos_unicos = sorted(set(int(a) for a in df["ano"].dropna().unique()))
    trimestres_unicos = sorted(df["trimestre"].dropna().unique())

    return df, meses_unicos, anos_unicos, trimestres_unicos

def separar_realizado_orcamento_postgresql(df: pd.DataFrame, origem_column: str = "source"):
    """Separa dados realizados e orçamentários para PostgreSQL"""
    df_real = df[df[origem_column] != "ORC"].copy()
    df_orc = df[df[origem_column] == "ORC"].copy()
    
    return df_real, df_orc

def calcular_totais_por_periodo_postgresql(df_real: pd.DataFrame, df_orc: pd.DataFrame, 
                                         meses_unicos: List[str], trimestres_unicos: List[str], 
                                         anos_unicos: List[int], conta_column: str, 
                                         valor_column: str = "value"):
    """Calcula totais por período para realizado e orçamento (PostgreSQL)"""
    
    # Realizado
    total_real_por_mes = {
        mes: df_real[df_real["mes"] == mes].groupby(conta_column)[valor_column].sum().to_dict()
        for mes in meses_unicos
    }

    # Orçamento
    total_orc_por_mes = {
        mes: df_orc[df_orc["mes"] == mes].groupby(conta_column)[valor_column].sum().to_dict()
        for mes in meses_unicos
    }

    # Trimestres
    total_real_por_tri = {}
    total_orc_por_tri = {}

    for tri in trimestres_unicos:
        meses_do_tri = df_real[df_real["trimestre"] == tri]["mes"].unique()
        soma_real = {}
        soma_orc = {}
        for mes in meses_do_tri:
            for conta, valor in total_real_por_mes.get(mes, {}).items():
                soma_real[conta] = soma_real.get(conta, 0) + valor
            for conta, valor in total_orc_por_mes.get(mes, {}).items():
                soma_orc[conta] = soma_orc.get(conta, 0) + valor
        total_real_por_tri[tri] = soma_real
        total_orc_por_tri[tri] = soma_orc

    # Anos
    total_real_por_ano = {}
    total_orc_por_ano = {}
    for ano in anos_unicos:
        meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
        soma_real = {}
        soma_orc = {}
        for mes in meses_do_ano:
            for conta, valor in total_real_por_mes.get(mes, {}).items():
                soma_real[conta] = soma_real.get(conta, 0) + valor
            for conta, valor in total_orc_por_mes.get(mes, {}).items():
                soma_orc[conta] = soma_orc.get(conta, 0) + valor
        total_real_por_ano[ano] = soma_real
        total_orc_por_ano[ano] = soma_orc

    # Totais gerais
    total_geral_real = {}
    total_geral_orc = {}
    for mes in meses_unicos:
        if mes in total_real_por_mes:
            for conta, valor in total_real_por_mes[mes].items():
                total_geral_real[conta] = total_geral_real.get(conta, 0) + valor
        if mes in total_orc_por_mes:
            for conta, valor in total_orc_por_mes[mes].items():
                total_geral_orc[conta] = total_geral_orc.get(conta, 0) + valor

    return {
        'total_real_por_mes': total_real_por_mes,
        'total_orc_por_mes': total_orc_por_mes,
        'total_real_por_tri': total_real_por_tri,
        'total_orc_por_tri': total_orc_por_tri,
        'total_real_por_ano': total_real_por_ano,
        'total_orc_por_ano': total_orc_por_ano,
        'total_geral_real': total_geral_real,
        'total_geral_orc': total_geral_orc
    }

def calcular_totalizadores_postgresql(valores_dict: Dict[str, float], estrutura: List[Dict[str, Any]]):
    """Calcula totalizadores dinamicamente baseados na estrutura (PostgreSQL)"""
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

def calcular_mom_postgresql(data: List[Dict], tipo: str) -> List[Dict]:
    """Calcula análise Month-over-Month para dados PostgreSQL"""
    if not data:
        return []
    
    # Agrupar por mês
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['mes'] = df['date'].dt.strftime('%Y-%m')
    
    # Agrupar por mês e somar valores
    monthly_totals = df.groupby('mes')['value'].sum().reset_index()
    monthly_totals = monthly_totals.sort_values('mes')
    
    mom_data = []
    for i, row in monthly_totals.iterrows():
        mes = row['mes']
        valor_atual = row['value']
        valor_anterior = monthly_totals.iloc[i-1]['value'] if i > 0 else None
        
        variacao_absoluta = None
        variacao_percentual = None
        
        if valor_anterior is not None:
            variacao_absoluta = valor_atual - valor_anterior
            if valor_anterior != 0:
                variacao_percentual = (variacao_absoluta / valor_anterior) * 100
        
        mom_data.append({
            "mes": mes,
            "valor_atual": valor_atual,
            "valor_anterior": valor_anterior,
            "variacao_absoluta": variacao_absoluta,
            "variacao_percentual": variacao_percentual
        })
    
    return mom_data

def calcular_pmr_pmp_postgresql(data: List[Dict], tipo: str) -> Dict[str, str]:
    """Calcula PMR/PMP para dados PostgreSQL"""
    if not data:
        return {"pmr": None, "pmp": None}
    
    # Para simplicidade, retornar valores padrão
    # Em uma implementação real, você calcularia baseado nas datas de vencimento
    if tipo == "receita":
        return {"pmr": "30 dias"}
    else:
        return {"pmp": "30 dias"}
