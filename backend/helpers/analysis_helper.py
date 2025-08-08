import pandas as pd
from financial_utils import (
    calcular_analise_vertical, calcular_analise_horizontal, 
    calcular_realizado_vs_orcado
)

def calcular_analises_completas(valores_mes, valores_tri, valores_ano, valores_total,
                               orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
                               meses_unicos, trimestres_unicos, anos_unicos, base_vertical=None):
    """Calcula todas as análises financeiras para um item"""
    
    def safe_real_vs_orcado(real, orcado):
        try:
            real_num = float(real) if real is not None else 0
            orcado_num = float(orcado) if orcado is not None else 0
            return calcular_realizado_vs_orcado(real_num, orcado_num)
        except (ValueError, TypeError):
            return "–"
    
    def safe_vertical(valor, base):
        try:
            if base is None or base == 0:
                return "–"
            return calcular_analise_vertical(valor, base)
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
            horizontal_mensais[mes] = calcular_analise_horizontal(valores_mes[mes], valores_mes[meses_unicos[i-1]])

    horizontal_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_trimestrais[tri] = "–"
        else:
            horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_tri[tri], valores_tri[trimestres_unicos[i-1]])

    horizontal_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_anuais[str(ano)] = "–"
        else:
            horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_ano[str(ano)], valores_ano[str(anos_unicos[i-1])])

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
            horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i-1]])

    horizontal_orcamentos_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_orcamentos_trimestrais[tri] = "–"
        else:
            horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i-1]])

    horizontal_orcamentos_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_orcamentos_anuais[str(ano)] = "–"
        else:
            horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i-1])])

    return {
        "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
        "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
        "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
        "real_vs_orcamento_total": real_vs_orcamento_total,
        "horizontal_mensais": horizontal_mensais,
        "horizontal_trimestrais": horizontal_trimestrais,
        "horizontal_anuais": horizontal_anuais,
        "vertical_mensais": vertical_mensais,
        "vertical_trimestrais": vertical_trimestrais,
        "vertical_anuais": vertical_anuais,
        "vertical_total": vertical_total,
        "vertical_orcamentos_mensais": vertical_orcamentos_mensais,
        "vertical_orcamentos_trimestrais": vertical_orcamentos_trimestrais,
        "vertical_orcamentos_anuais": vertical_orcamentos_anuais,
        "vertical_orcamentos_total": vertical_orcamentos_total,
        "horizontal_orcamentos_mensais": horizontal_orcamentos_mensais,
        "horizontal_orcamentos_trimestrais": horizontal_orcamentos_trimestrais,
        "horizontal_orcamentos_anuais": horizontal_orcamentos_anuais
    }

def calcular_pmr_pmp(df_con, origem):
    """Calcula PMR (Prazo Médio de Recebimento) e PMP (Prazo Médio de Pagamento)"""
    pmr = None
    pmp = None
    
    # Identificar coluna de data de caixa
    data_caixa_col = None
    if "data" in df_con.columns and "vencimento" in df_con.columns:
        data_caixa_col = df_con["data"].combine_first(df_con["vencimento"])
    elif "data" in df_con.columns:
        data_caixa_col = df_con["data"]
    elif "vencimento" in df_con.columns:
        data_caixa_col = df_con["vencimento"]

    # Calcular PMR (Prazo Médio de Recebimento)
    if origem == "CAR" and data_caixa_col is not None and "competencia" in df_con.columns:
        mask = (
            df_con["origem"] == "CAR"
            ) & (
            data_caixa_col.notna()
            ) & (
            df_con["competencia"].notna()
            )
        df_pmr = df_con[mask].copy()
        if not df_pmr.empty:
            df_pmr["data_caixa"] = data_caixa_col[mask]
            df_pmr["competencia"] = pd.to_datetime(df_pmr["competencia"])
            df_pmr["diferenca_dias"] = (df_pmr["data_caixa"] - df_pmr["competencia"]).dt.days
            # PMR ponderado pelo valor
            df_pmr_valid = df_pmr.dropna(subset=["diferenca_dias", "valor"])
            if not df_pmr_valid.empty and df_pmr_valid["valor"].sum() != 0:
                pmr = (df_pmr_valid["diferenca_dias"] * df_pmr_valid["valor"]).sum() / df_pmr_valid["valor"].sum()

    # Calcular PMP (Prazo Médio de Pagamento)
    if origem == "CAP" and data_caixa_col is not None and "competencia" in df_con.columns:
        mask = (
            df_con["origem"] == "CAP"
            ) & (
            (df_con["dfc_n1"].fillna("") != "Movimentação entre Contas")
            ) & (
            data_caixa_col.notna()
            ) & (
            df_con["competencia"].notna()
            )
        df_pmp = df_con[mask].copy()
        if not df_pmp.empty:
            df_pmp["data_caixa"] = data_caixa_col[mask]
            df_pmp["competencia"] = pd.to_datetime(df_pmp["competencia"])
            df_pmp["diferenca_dias"] = (df_pmp["data_caixa"] - df_pmp["competencia"]).dt.days
            # PMP ponderado pelo valor
            df_pmp_valid = df_pmp.dropna(subset=["diferenca_dias", "valor"])
            if not df_pmp_valid.empty and df_pmp_valid["valor"].sum() != 0:
                pmp = (df_pmp_valid["diferenca_dias"] * df_pmp_valid["valor"]).sum() / df_pmp_valid["valor"].sum()

    return {
        "pmr": f"{int(pmr)} dias" if pmr is not None else None,
        "pmp": f"{int(pmp)} dias" if pmp is not None else None
    } 