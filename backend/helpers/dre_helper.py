import pandas as pd
from .data_processor import calcular_totais_por_periodo
from .analysis_helper import calcular_analises_completas
from .structure_helper import carregar_estrutura_dre

def criar_linha_conta_dre(nome, tipo, valores_mensais, valores_trimestrais, valores_anuais,
                          orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                          valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                          get_classificacoes):
    """Cria uma linha de conta para DRE"""
    
    valores_mes = {mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos}
    valores_tri = {tri: round(valores_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
    valores_ano = {str(ano): round(valores_anuais[str(ano)][nome], 0) for ano in anos_unicos}
    orcamentos_mes = {mes: round(orcamentos_mensais[mes][nome], 0) for mes in meses_unicos}
    orcamentos_tri = {tri: round(orcamentos_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
    orcamentos_ano = {str(ano): round(orcamentos_anuais[str(ano)][nome], 0) for ano in anos_unicos}

    valores_total = valores_totais[nome]
    orcamento_total = orcamentos_totais[nome]

    # Calcular análises usando faturamento como base vertical
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, valores_total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
        meses_unicos, trimestres_unicos, anos_unicos,
        valores_totais.get("Faturamento", 0)
    )

    return {
        "tipo": tipo,
        "nome": nome,
        "valor": valores_total,
        "valores_mensais": valores_mes,
        "valores_trimestrais": valores_tri,
        "valores_anuais": valores_ano,
        "orcamentos_mensais": orcamentos_mes,
        "orcamentos_trimestrais": orcamentos_tri,
        "orcamentos_anuais": orcamentos_ano,
        "orcamento_total": orcamento_total,
        **analises,
        "classificacoes": get_classificacoes(nome)
    }

def calcular_linha_totalizador_dre(nome, func, tipo="=", valores_totais=None, valores_mensais=None,
                                  valores_trimestrais=None, valores_anuais=None, orcamentos_totais=None,
                                  orcamentos_mensais=None, orcamentos_trimestrais=None, orcamentos_anuais=None,
                                  meses_unicos=None, trimestres_unicos=None, anos_unicos=None):
    """Calcula uma linha de totalizador para DRE"""
    
    if valores_totais is None:
        valores_totais = {}
    if valores_mensais is None:
        valores_mensais = {}
    if valores_trimestrais is None:
        valores_trimestrais = {}
    if valores_anuais is None:
        valores_anuais = {}
    if orcamentos_totais is None:
        orcamentos_totais = {}
    if orcamentos_mensais is None:
        orcamentos_mensais = {}
    if orcamentos_trimestrais is None:
        orcamentos_trimestrais = {}
    if orcamentos_anuais is None:
        orcamentos_anuais = {}
    if meses_unicos is None:
        meses_unicos = []
    if trimestres_unicos is None:
        trimestres_unicos = []
    if anos_unicos is None:
        anos_unicos = []
    
    total = round(func(valores_totais), 0)
    valores_mes = {mes: round(func(valores_mensais[mes]), 0) for mes in meses_unicos}
    valores_tri = {tri: round(func(valores_trimestrais[tri]), 0) for tri in trimestres_unicos}
    valores_ano = {str(ano): round(func(valores_anuais[str(ano)]), 0) for ano in anos_unicos}
    orcamentos_mes = {mes: round(func(orcamentos_mensais[mes]), 0) for mes in meses_unicos}
    orcamentos_tri = {tri: round(func(orcamentos_trimestrais[tri]), 0) for tri in trimestres_unicos}
    orcamentos_ano = {str(ano): round(func(orcamentos_anuais[str(ano)]), 0) for ano in anos_unicos}
    orcamento_total = round(func(orcamentos_totais), 0)

    # Calcular análises
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
        meses_unicos, trimestres_unicos, anos_unicos,
        valores_totais.get("Faturamento", 0)
    )

    return {
        "tipo": tipo,
        "nome": nome,
        "valor": total,
        "valores_mensais": valores_mes,
        "valores_trimestrais": valores_tri,
        "valores_anuais": valores_ano,
        "orcamentos_mensais": orcamentos_mes,
        "orcamentos_trimestrais": orcamentos_tri,
        "orcamentos_anuais": orcamentos_ano,
        "orcamento_total": orcamento_total,
        **analises,
        "classificacoes": []
    }

def get_classificacoes_dre(df_real, df_orc, dre_n2_name, meses_unicos, trimestres_unicos, anos_unicos,
                          valores_mensais, valores_trimestrais, valores_anuais, total_geral_real, total_geral_orc):
    """Obtém classificações para uma conta DRE específica"""
    sub_df_real = df_real[df_real["DRE_n2"] == dre_n2_name]
    sub_df_orc = df_orc[df_orc["DRE_n2"] == dre_n2_name]
    if sub_df_real.empty:
        return []

    classificacoes = []
    # Obter todas as classificações únicas (de realizado e orçamento)
    classificacoes_unicas = set(sub_df_real["classificacao"].unique())
    if not sub_df_orc.empty:
        classificacoes_unicas.update(sub_df_orc["classificacao"].unique())

    for classificacao in classificacoes_unicas:
        # Dados realizados
        grupo_real = sub_df_real[sub_df_real["classificacao"] == classificacao]
        
        # Dados orçamentários
        grupo_orc = sub_df_orc[sub_df_orc["classificacao"] == classificacao]

        # Calcular valores por período - REALIZADO
        valores_mes = {}
        for mes in meses_unicos:
            valores_mes[mes] = grupo_real[grupo_real["mes_ano"] == mes]["valor_original"].sum()

        valores_tri = {}
        for tri in trimestres_unicos:
            meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
            soma = sum(valores_mes.get(mes, 0) for mes in meses_do_tri)
            valores_tri[tri] = soma

        valores_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma = sum(valores_mes.get(mes, 0) for mes in meses_do_ano)
            valores_ano[str(ano)] = soma

        total_real = grupo_real["valor_original"].sum()

        # Calcular valores por período - ORÇAMENTO
        orcamentos_mes = {}
        for mes in meses_unicos:
            orcamentos_mes[mes] = grupo_orc[grupo_orc["mes_ano"] == mes]["valor_original"].sum()

        orcamentos_tri = {}
        for tri in trimestres_unicos:
            meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
            soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_tri)
            orcamentos_tri[tri] = soma

        orcamentos_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_ano)
            orcamentos_ano[str(ano)] = soma

        total_orc = grupo_orc["valor_original"].sum()

        # Calcular análises
        analises = calcular_analises_completas(
            valores_mes, valores_tri, valores_ano, total_real,
            orcamentos_mes, orcamentos_tri, orcamentos_ano, total_orc,
            meses_unicos, trimestres_unicos, anos_unicos,
            total_geral_real.get("Faturamento", 0)
        )

        classificacoes.append({
            "nome": classificacao,
            "valor": total_real,
            "valores_mensais": valores_mes,
            "valores_trimestrais": valores_tri,
            "valores_anuais": valores_ano,
            "orcamentos_mensais": orcamentos_mes,
            "orcamentos_trimestrais": orcamentos_tri,
            "orcamentos_anuais": orcamentos_ano,
            **analises
        })
    return classificacoes 