from fastapi import APIRouter
import pandas as pd
import time
import os
from financial_utils import (
    calcular_analise_vertical, calcular_analise_horizontal, 
    calcular_realizado_vs_orcado, calcular_totalizadores,
    processar_periodos_financeiros, calcular_valores_por_periodo,
    agregar_por_periodo_superior, calcular_analises_completas,
    formatar_item_financeiro
)
import pandas as pd
import time
import os

# --- CACHE GLOBAL PARA O DATAFRAME ---
_df_cache = {
    "df": None,
    "last_loaded": 0,
    "last_mtime": 0,
}
CACHE_TIMEOUT = 60  # segundos

def get_cached_df(filename="financial-data-roriz.xlsx"):
    global _df_cache
    try:
        mtime = os.path.getmtime(filename)
    except Exception:
        return None
    now = time.time()
    # Recarrega se: nunca carregado, arquivo mudou, ou timeout
    if (
        _df_cache["df"] is None
        or _df_cache["last_mtime"] != mtime
        or now - _df_cache["last_loaded"] > CACHE_TIMEOUT
    ):
        try:
            df = pd.read_excel(filename)
            _df_cache["df"] = df
            _df_cache["last_loaded"] = now
            _df_cache["last_mtime"] = mtime
        except Exception:
            _df_cache["df"] = None
    return _df_cache["df"]

router = APIRouter()

from fastapi import Request

@router.get("/dre")
def get_dre_data(request: Request):
    filename = "financial-data-roriz.xlsx"


    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Filtro por mês, se fornecido na query string
        mes_param = request.query_params.get("mes")
        if mes_param:
            # Garante que a coluna mes_ano existe antes de filtrar
            date_column = next((col for col in df.columns if col.lower() == "competencia"), None)
            if date_column:
                df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
                df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
                df = df[df["mes_ano"] == mes_param]
            else:
                return {"error": "Coluna de competência não encontrada para filtro de mês."}

        # Validação das colunas obrigatórias (incluindo 'origem')
        required_columns = ["DRE_n2", "valor_original", "classificacao", "origem"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        date_column = next((col for col in df.columns if col.lower() == "competencia"), None)
        if not date_column:
            return {"error": "Coluna de competência não encontrada"}

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
        df["ano"] = df[date_column].dt.year
        df["trimestre"] = df[date_column].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")

        df["valor_original"] = pd.to_numeric(df["valor_original"], errors="coerce")
        df = df.dropna(subset=[date_column, "valor_original"])

        meses_unicos = sorted(df["mes_ano"].dropna().unique())
        anos_unicos = sorted(set(int(a) for a in df["ano"].dropna().unique()))
        trimestres_unicos = sorted(df["trimestre"].dropna().unique())

        # Separar realizado e orçamento com validação
        df_real = df[df["origem"] != "ORC"].copy()
        df_orc = df[df["origem"] == "ORC"].copy()

        if df_real.empty:
            return {"error": "Não foram encontrados dados realizados na planilha"}
        if df_orc.empty:
            return {"error": "Não foram encontrados dados orçamentários na planilha"}

        # Realizado
        total_real_por_mes = {
            mes: df_real[df_real["mes_ano"] == mes].groupby("DRE_n2")["valor_original"].sum().to_dict()
            for mes in meses_unicos
        }

        # Orçamento
        total_orc_por_mes = {
            mes: df_orc[df_orc["mes_ano"] == mes].groupby("DRE_n2")["valor_original"].sum().to_dict()
            for mes in meses_unicos
        }

        total_real_por_tri = {}
        total_orc_por_tri = {}

        for tri in trimestres_unicos:
            meses_do_tri = df[df["trimestre"] == tri]["mes_ano"].unique()
            soma_real = {}
            soma_orc = {}
            for mes in meses_do_tri:
                for conta, valor in total_real_por_mes.get(mes, {}).items():
                    soma_real[conta] = soma_real.get(conta, 0) + valor
                for conta, valor in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[conta] = soma_orc.get(conta, 0) + valor
            total_real_por_tri[tri] = soma_real
            total_orc_por_tri[tri] = soma_orc

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

        total_geral_real = {}
        total_geral_orc = {}
        for mes in meses_unicos:
            if mes in total_real_por_mes:
                for conta, valor in total_real_por_mes[mes].items():
                    total_geral_real[conta] = total_geral_real.get(conta, 0) + valor
            if mes in total_orc_por_mes:
                for conta, valor in total_orc_por_mes[mes].items():
                    total_geral_orc[conta] = total_geral_orc.get(conta, 0) + valor

        contas_dre = [
            ("Faturamento", "+"),
            ("Tributos e deduções sobre a receita", "-"),
            ("Custo com Importação", "-"),
            ("Custo com Mercadoria Interna", "-"),
            ("Despesas Administrativa", "-"),
            ("Despesas com Pessoal", "-"),
            ("Despesas com Ocupação", "-"),
            ("Despesas comercial", "-"),
            ("Despesas com E-commerce", "-"),
            ("Depreciação", "-"),
            ("Amortização", "-"),
            ("Receitas Financeiras", "+"),
            ("Despesas Financeiras", "-"),
            ("Receitas não operacionais", "+"),
            ("Despesas não operacionais", "-"),
            ("IRPJ", "-"),
            ("CSLL", "-")
        ]

        valores_mensais = {
            mes: {nome: total_real_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }
        orcamentos_mensais = {
            mes: {nome: total_orc_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }

        valores_trimestrais = {
            tri: {nome: total_real_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }
        orcamentos_trimestrais = {
            tri: {nome: total_orc_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }

        valores_anuais = {
            str(ano): {nome: total_real_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }
        orcamentos_anuais = {
            str(ano): {nome: total_orc_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }

        # Definir variáveis de orçamento no escopo correto
        orcamentos_mes = {
            mes: {nome: total_orc_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }

        orcamentos_tri = {
            tri: {nome: total_orc_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }

        orcamentos_ano = {
            str(ano): {nome: total_orc_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }

        orcamento_total = {nome: total_geral_orc.get(nome, 0.0) for nome, _ in contas_dre}

        def get_classificacoes(dre_n2_name):
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
                    meses_do_tri = df[df["trimestre"] == tri]["mes_ano"].unique()
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
                    meses_do_tri = df[df["trimestre"] == tri]["mes_ano"].unique()
                    soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_tri)
                    orcamentos_tri[tri] = soma

                orcamentos_ano = {}
                for ano in anos_unicos:
                    meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
                    soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_ano)
                    orcamentos_ano[str(ano)] = soma

                total_orc = grupo_orc["valor_original"].sum()

                # Calcular análises verticais
                vertical_mensais = {}
                for mes in meses_unicos:
                    vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], valores_mensais[mes]["Faturamento"])

                vertical_trimestrais = {}
                for tri in trimestres_unicos:
                    vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], valores_trimestrais[tri]["Faturamento"])

                vertical_anuais = {}
                for ano in anos_unicos:
                    vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], valores_anuais[str(ano)]["Faturamento"])

                vertical_total = calcular_analise_vertical(total_real, total_geral_real.get("Faturamento", 0))

                # Calcular análises verticais para orçamento
                vertical_mensais_orcamento = {}
                for mes in meses_unicos:
                    vertical_mensais_orcamento[mes] = calcular_analise_vertical(orcamentos_mes[mes], orcamentos_mensais[mes]["Faturamento"])

                vertical_trimestrais_orcamento = {}
                for tri in trimestres_unicos:
                    vertical_trimestrais_orcamento[tri] = calcular_analise_vertical(orcamentos_tri[tri], orcamentos_trimestrais[tri]["Faturamento"])

                vertical_anuais_orcamento = {}
                for ano in anos_unicos:
                    vertical_anuais_orcamento[str(ano)] = calcular_analise_vertical(orcamentos_ano[str(ano)], orcamentos_anuais[str(ano)]["Faturamento"])

                vertical_orcamentos_total = calcular_analise_vertical(total_orc, total_geral_orc.get("Faturamento", 0))

                # Calcular análises horizontais
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

                # Calcular análises horizontais para orçamento
                horizontal_mensais_orcamento = {}
                for i, mes in enumerate(meses_unicos):
                    if i == 0:
                        horizontal_mensais_orcamento[mes] = "–"
                    else:
                        horizontal_mensais_orcamento[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i-1]])

                horizontal_trimestrais_orcamento = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i == 0:
                        horizontal_trimestrais_orcamento[tri] = "–"
                    else:
                        horizontal_trimestrais_orcamento[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i-1]])

                horizontal_anuais_orcamento = {}
                for i, ano in enumerate(anos_unicos):
                    if i == 0:
                        horizontal_anuais_orcamento[str(ano)] = "–"
                    else:
                        horizontal_anuais_orcamento[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i-1])])

                classificacoes.append({
                    "nome": classificacao,
                    "valor": total_real,
                    "valores_mensais": valores_mes,
                    "valores_trimestrais": valores_tri,
                    "valores_anuais": valores_ano,
                    "orcamentos_mensais": orcamentos_mes,
                    "orcamentos_trimestrais": orcamentos_tri,
                    "orcamentos_anuais": orcamentos_ano,
                    "vertical_total": vertical_total,
                    "vertical_mensais": vertical_mensais,
                    "vertical_trimestrais": vertical_trimestrais,
                    "vertical_anuais": vertical_anuais,
                    "vertical_mensais_orcamento": vertical_mensais_orcamento,
                    "vertical_trimestrais_orcamento": vertical_trimestrais_orcamento,
                    "vertical_anuais_orcamento": vertical_anuais_orcamento,
                    "vertical_orcamentos_total": vertical_orcamentos_total,
                    "horizontal_mensais": horizontal_mensais,
                    "horizontal_trimestrais": horizontal_trimestrais,
                    "horizontal_anuais": horizontal_anuais,
                    "horizontal_mensais_orcamento": horizontal_mensais_orcamento,
                    "horizontal_trimestrais_orcamento": horizontal_trimestrais_orcamento,
                    "horizontal_anuais_orcamento": horizontal_anuais_orcamento
                })
            return classificacoes

        valores_totais = {nome: total_geral_real.get(nome, 0.0) for nome, _ in contas_dre}
        orcamentos_totais = {nome: total_geral_orc.get(nome, 0.0) for nome, _ in contas_dre}

        def criar_linha_conta(nome, tipo):
            valores_mes = {mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos}
            valores_tri = {tri: round(valores_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
            valores_ano = {str(ano): round(valores_anuais[str(ano)][nome], 0) for ano in anos_unicos}
            orcamentos_mes = {mes: round(orcamentos_mensais[mes][nome], 0) for mes in meses_unicos}
            orcamentos_tri = {tri: round(orcamentos_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
            orcamentos_ano = {str(ano): round(orcamentos_anuais[str(ano)][nome], 0) for ano in anos_unicos}

            valores_total = valores_totais[nome]
            orcamento_total = orcamentos_totais[nome]

            ### Real vs Orçado
            real_vs_orcamento_mensais = {mes: calcular_realizado_vs_orcado(valores_mes[mes], orcamentos_mes[mes]) for mes in meses_unicos}
            real_vs_orcamento_trimestrais = {tri: calcular_realizado_vs_orcado(valores_tri[tri], orcamentos_tri[tri]) for tri in trimestres_unicos}
            real_vs_orcamento_anuais = {str(ano): calcular_realizado_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)]) for ano in anos_unicos}
            real_vs_orcamento_total = calcular_realizado_vs_orcado(valores_total, orcamento_total)

            ### Horizontal Realizado
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

            ### Vertical Realizado
            vertical_mensais = {}
            for mes in meses_unicos:
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], valores_mensais[mes]["Faturamento"])

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], valores_trimestrais[tri]["Faturamento"])

            vertical_anuais = {}
            for ano in anos_unicos:
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], valores_anuais[str(ano)]["Faturamento"])

            vertical_total = calcular_analise_vertical(valores_total, valores_totais["Faturamento"])

            ### Vertical Orçamento
            vertical_orcamentos_mensais = {}
            for mes in meses_unicos:
                vertical_orcamentos_mensais[mes] = calcular_analise_vertical(orcamentos_mes[mes], orcamentos_mensais[mes]["Faturamento"])

            vertical_orcamentos_trimestrais = {}
            for tri in trimestres_unicos:
                vertical_orcamentos_trimestrais[tri] = calcular_analise_vertical(orcamentos_tri[tri], orcamentos_trimestrais[tri]["Faturamento"])

            vertical_orcamentos_anuais = {}
            for ano in anos_unicos:
                vertical_orcamentos_anuais[str(ano)] = calcular_analise_vertical(orcamentos_ano[str(ano)], orcamentos_anuais[str(ano)]["Faturamento"])

            vertical_orcamentos_total = calcular_analise_vertical(orcamento_total, orcamentos_totais["Faturamento"])

            ### Horizontal Orçamento
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
                "vertical_mensais": vertical_mensais,
                "vertical_trimestrais": vertical_trimestrais,
                "vertical_anuais": vertical_anuais,
                "vertical_total": vertical_total,
                "horizontal_mensais": horizontal_mensais,
                "horizontal_trimestrais": horizontal_trimestrais,
                "horizontal_anuais": horizontal_anuais,
                "vertical_orcamentos_mensais": vertical_orcamentos_mensais,
                "vertical_orcamentos_trimestrais": vertical_orcamentos_trimestrais,
                "vertical_orcamentos_anuais": vertical_orcamentos_anuais,
                "vertical_orcamentos_total": vertical_orcamentos_total,
                "horizontal_orcamentos_mensais": horizontal_orcamentos_mensais,
                "horizontal_orcamentos_trimestrais": horizontal_orcamentos_trimestrais,
                "horizontal_orcamentos_anuais": horizontal_orcamentos_anuais,
                "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                "real_vs_orcamento_total": real_vs_orcamento_total,
                "classificacoes": get_classificacoes(nome)
            }

        def calcular_linha(nome, func, tipo="="):
            total = round(func(valores_totais), 0)
            valores_mes = {mes: round(func(valores_mensais[mes]), 0) for mes in meses_unicos}
            valores_tri = {tri: round(func(valores_trimestrais[tri]), 0) for tri in trimestres_unicos}
            valores_ano = {str(ano): round(func(valores_anuais[str(ano)]), 0) for ano in anos_unicos}
            orcamentos_mes = {mes: round(func(orcamentos_mensais[mes]), 0) for mes in meses_unicos}
            orcamentos_tri = {tri: round(func(orcamentos_trimestrais[tri]), 0) for tri in trimestres_unicos}
            orcamentos_ano = {str(ano): round(func(orcamentos_anuais[str(ano)]), 0) for ano in anos_unicos}
            orcamento_total = round(func(orcamentos_totais), 0)

            # Real vs Orçamento - CORRIGIDO
            real_vs_orcamento_mensais = {}
            for mes in meses_unicos:
                real_vs_orcamento_mensais[mes] = calcular_realizado_vs_orcado(valores_mes[mes], orcamentos_mes[mes])

            real_vs_orcamento_trimestrais = {}
            for tri in trimestres_unicos:
                real_vs_orcamento_trimestrais[tri] = calcular_realizado_vs_orcado(valores_tri[tri], orcamentos_tri[tri])

            real_vs_orcamento_anuais = {}
            for ano in anos_unicos:
                real_vs_orcamento_anuais[str(ano)] = calcular_realizado_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)])

            real_vs_orcamento_total = calcular_realizado_vs_orcado(total, orcamento_total)

            # Análise Horizontal - CORRIGIDO
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

            # Análise Vertical - CORRIGIDO
            vertical_mensais = {}
            for mes in meses_unicos:
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], valores_mensais[mes]["Faturamento"])

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], valores_trimestrais[tri]["Faturamento"])

            vertical_anuais = {}
            for ano in anos_unicos:
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], valores_anuais[str(ano)]["Faturamento"])

            receita_total = valores_totais["Faturamento"]
            vertical_total = calcular_analise_vertical(total, receita_total)

            # Vertical Orçamento
            vertical_orcamentos_mensais = {}
            vertical_orcamentos_trimestrais = {}
            vertical_orcamentos_anuais = {}
            vertical_orcamentos_total = "–"  # Totalizadores não têm análise vertical

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
                "vertical_mensais": vertical_mensais,
                "vertical_trimestrais": vertical_trimestrais,
                "vertical_anuais": vertical_anuais,
                "vertical_total": vertical_total,
                "horizontal_mensais": horizontal_mensais,
                "horizontal_trimestrais": horizontal_trimestrais,
                "horizontal_anuais": horizontal_anuais,
                "vertical_orcamentos_mensais": vertical_orcamentos_mensais,
                "vertical_orcamentos_trimestrais": vertical_orcamentos_trimestrais,
                "vertical_orcamentos_anuais": vertical_orcamentos_anuais,
                "vertical_orcamentos_total": vertical_orcamentos_total,
                "horizontal_orcamentos_mensais": horizontal_orcamentos_mensais,
                "horizontal_orcamentos_trimestrais": horizontal_orcamentos_trimestrais,
                "horizontal_orcamentos_anuais": horizontal_orcamentos_anuais,
                "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                "real_vs_orcamento_total": real_vs_orcamento_total,
                "classificacoes": get_classificacoes(nome)
            }

        result = []
        result.append(criar_linha_conta("Faturamento", "+"))
        result.append(calcular_linha("Receita Bruta", lambda v: v["Faturamento"]))
        result.append(criar_linha_conta("Tributos e deduções sobre a receita", "-"))
        result.append(calcular_linha("Receita Líquida", lambda v: v["Faturamento"] + v["Tributos e deduções sobre a receita"]))

        for nome in ["Custo com Importação", "Custo com Mercadoria Interna"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("Resultado Bruto", lambda v: (
            v["Faturamento"] + v["Tributos e deduções sobre a receita"] + v["Custo com Importação"] + v["Custo com Mercadoria Interna"]
        )))

        for nome in ["Despesas Administrativa", "Despesas com Pessoal", "Despesas com Ocupação", "Despesas comercial", "Despesas com E-commerce"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("EBITDA", lambda v: (
            v["Faturamento"] + v["Tributos e deduções sobre a receita"] + v["Custo com Importação"] + v["Custo com Mercadoria Interna"]
            + v["Despesas Administrativa"] + v["Despesas com Pessoal"]
            + v["Despesas com Ocupação"] + v["Despesas comercial"] + v["Despesas com E-commerce"]
        )))

        for nome in ["Depreciação", "Amortização"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("EBIT", lambda v: (
            v["Faturamento"] + v["Tributos e deduções sobre a receita"] + v["Custo com Importação"] + v["Custo com Mercadoria Interna"]
            + v["Despesas Administrativa"] + v["Despesas com Pessoal"]
            + v["Despesas com Ocupação"] + v["Despesas comercial"] + v["Despesas com E-commerce"]
            + v["Depreciação"] + v["Amortização"]
        )))

        for nome in ["Receitas Financeiras", "Despesas Financeiras",
                     "Receitas não operacionais", "Despesas não operacionais"]:
            result.append(criar_linha_conta(nome, "+" if "Receitas" in nome else "-"))

        result.append(calcular_linha("Resultado Financeiro", lambda v: (
            v["Faturamento"] + v["Tributos e deduções sobre a receita"] + v["Custo com Importação"] + v["Custo com Mercadoria Interna"]
            + v["Despesas Administrativa"] + v["Despesas com Pessoal"]
            + v["Despesas com Ocupação"] + v["Despesas comercial"] + v["Despesas com E-commerce"]
            + v["Depreciação"] + v["Amortização"]
            + v["Receitas Financeiras"] + v["Despesas Financeiras"]
            + v["Receitas não operacionais"] + v["Despesas não operacionais"]
        )))

        for nome in ["IRPJ", "CSLL"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("Resultado Líquido", lambda v: (
            v["Faturamento"] + v["Tributos e deduções sobre a receita"] + v["Custo com Importação"] + v["Custo com Mercadoria Interna"]
            + v["Despesas Administrativa"] + v["Despesas com Pessoal"]
            + v["Despesas com Ocupação"] + v["Despesas comercial"] + v["Despesas com E-commerce"]
            + v["Depreciação"] + v["Amortização"]
            + v["Receitas Financeiras"] + v["Despesas Financeiras"]
            + v["Receitas não operacionais"] + v["Despesas não operacionais"]
            + v["IRPJ"] + v["CSLL"]
        )))

        # Calcular análise vertical para as classificações
        for item in result:
            if "classificacoes" in item and item["classificacoes"]:
                for classificacao in item["classificacoes"]:
                    classificacao["vertical_total"] = calcular_analise_vertical(
                        classificacao["valor"], valores_totais["Faturamento"]
                    )

        return {
            "meses": meses_unicos,
            "trimestres": trimestres_unicos,
            "anos": anos_unicos,
            "data": result,
            "orcamentos_mensais": orcamentos_mes,
            "orcamentos_trimestrais": orcamentos_tri,
            "orcamentos_anuais": orcamentos_ano,
            "orcamento_total": orcamento_total,
        }

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}