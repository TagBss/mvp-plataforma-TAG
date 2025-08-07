import pandas as pd
from financial_utils import (
    calcular_analise_vertical, calcular_analise_horizontal, 
    calcular_realizado_vs_orcado, calcular_totalizadores
)

def processar_dados_financeiros(df, date_column, valor_column="valor"):
    """Processa dados financeiros básicos"""
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
    df["ano"] = df[date_column].dt.year
    df["trimestre"] = df[date_column].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")

    df[valor_column] = pd.to_numeric(df[valor_column], errors="coerce")
    df = df.dropna(subset=[date_column, valor_column])

    meses_unicos = sorted(df["mes_ano"].dropna().unique())
    anos_unicos = sorted(set(int(a) for a in df["ano"].dropna().unique()))
    trimestres_unicos = sorted(df["trimestre"].dropna().unique())

    return df, meses_unicos, anos_unicos, trimestres_unicos

def separar_realizado_orcamento(df, origem_column="origem"):
    """Separa dados realizados e orçamentários"""
    df_real = df[df[origem_column] != "ORC"].copy()
    df_orc = df[df[origem_column] == "ORC"].copy()
    
    return df_real, df_orc

def calcular_totais_por_periodo(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos, 
                               conta_column, valor_column="valor"):
    """Calcula totais por período para realizado e orçamento"""
    
    # Realizado
    total_real_por_mes = {
        mes: df_real[df_real["mes_ano"] == mes].groupby(conta_column)[valor_column].sum().to_dict()
        for mes in meses_unicos
    }

    # Orçamento
    total_orc_por_mes = {
        mes: df_orc[df_orc["mes_ano"] == mes].groupby(conta_column)[valor_column].sum().to_dict()
        for mes in meses_unicos
    }

    # Trimestres
    total_real_por_tri = {}
    total_orc_por_tri = {}

    for tri in trimestres_unicos:
        meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
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

def calcular_totalizadores(valores_dict, estrutura):
    """Calcula totalizadores dinamicamente baseados na estrutura"""
    totalizadores = {}
    
    for item in estrutura:
        totalizador_nome = item["totalizador"]
        if totalizador_nome and totalizador_nome not in totalizadores:
            totalizadores[totalizador_nome] = 0
        
        if totalizador_nome:
            valor_conta = valores_dict.get(item["nome"], 0)
            if item["tipo"] in ["+", "+/-"]:
                totalizadores[totalizador_nome] += valor_conta
            elif item["tipo"] == "-":
                totalizadores[totalizador_nome] -= valor_conta
    
    return totalizadores

def calcular_mom(df_filtrado, date_column, origem):
    """Calcula variação Month over Month (MoM)"""
    try:
        # Agrupar por mês e somar valores
        df_mensal = df_filtrado.groupby(
            df_filtrado[date_column].dt.to_period('M')
        )['valor'].sum().reset_index()
        
        # Ordenar por data
        df_mensal = df_mensal.sort_values(date_column)
        
        # Calcular variação MoM
        df_mensal['valor_anterior'] = df_mensal['valor'].shift(1)
        df_mensal['variacao_absoluta'] = df_mensal['valor'] - df_mensal['valor_anterior']
        df_mensal['variacao_percentual'] = (
            (df_mensal['valor'] - df_mensal['valor_anterior']) / 
            df_mensal['valor_anterior'] * 100
        ).round(2)
        
        # Preparar dados para retorno
        mom_data = []
        for _, row in df_mensal.iterrows():
            mom_data.append({
                "mes": str(row[date_column]),
                "valor_atual": round(row['valor'], 2),
                "valor_anterior": round(row['valor_anterior'], 2) if pd.notna(row['valor_anterior']) else None,
                "variacao_absoluta": round(row['variacao_absoluta'], 2) if pd.notna(row['variacao_absoluta']) else None,
                "variacao_percentual": row['variacao_percentual'] if pd.notna(row['variacao_percentual']) else None
            })
        
        return mom_data
        
    except Exception as e:
        return [] 