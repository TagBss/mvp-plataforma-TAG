from fastapi import APIRouter
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

@router.get("/dfc")
def get_dfc_data():
    filename = "financial-data-roriz.xlsx"

    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Validação das colunas obrigatórias (incluindo 'origem')
        required_columns = ["DFC_n2", "valor", "classificacao", "origem"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        date_column = next((col for col in df.columns if col.lower() == "data"), None)
        if not date_column:
            return {"error": "Coluna de competência não encontrada"}

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
        df["ano"] = df[date_column].dt.year
        df["trimestre"] = df[date_column].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")

        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=[date_column, "valor"])

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
            mes: df_real[df_real["mes_ano"] == mes].groupby("DFC_n2")["valor"].sum().to_dict()
            for mes in meses_unicos
        }

        # Orçamento
        total_orc_por_mes = {
            mes: df_orc[df_orc["mes_ano"] == mes].groupby("DFC_n2")["valor"].sum().to_dict()
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

        contas_dfc = [
            ("Recebimentos Operacionais", "+"),
            ("Tributos sobre vendas", "-"),
            ("Custos", "-"),
            ("Desembolsos Operacionais", "-"),
            ("Despesas Administrativa", "-"),
            ("Despesas com Pessoal", "-"),
            ("Despesas com E-commerce", "-"),
            ("Despesas com Comercial", "-"),
            ("Despesas com Viagem", "-"),
            ("Despesas com Ocupação", "-"),
            ("Adiantamentos entrada", "+"),
            ("Adiantamentos saída", "-"),
            ("Impostos", "-"),
            ("Investimento Comercial", "-"),
            ("Investimento em Desenvolvimento", "-"),
            ("Imobilizado", "-"),
            ("Intangível", "-"),
            ("Marcas e Patentes", "-"),
            ("Recebimento de Empréstimos", "+"),
            ("Receitas não operacionais", "+"),
            ("Despesas não operacionais", "-"),
            ("Pagamento de Empréstimos", "-"),
            ("Parcelamentos de Impostos", "-"),
            ("Aporte de capital", "+"),
            ("Distribuição de lucro", "-"),
            ("Aplicação Automática", "-"),
            ("Resgate Automático", "+"),
            ("Transferência Entrada", "+"),
            ("Transferência Saída", "-"),
            ("Empréstimo de Mútuo - Crédito", "+"),
            ("Empréstimo de Mútuo - Débito", "-"),
        ]

        valores_mensais = {
            mes: {nome: total_real_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for mes in meses_unicos
        }
        orcamentos_mensais = {
            mes: {nome: total_orc_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for mes in meses_unicos
        }

        valores_trimestrais = {
            tri: {nome: total_real_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for tri in trimestres_unicos
        }
        orcamentos_trimestrais = {
            tri: {nome: total_orc_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for tri in trimestres_unicos
        }

        valores_anuais = {
            str(ano): {nome: total_real_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for ano in anos_unicos
        }
        orcamentos_anuais = {
            str(ano): {nome: total_orc_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for ano in anos_unicos
        }

        # Definir variáveis de orçamento no escopo correto
        orcamentos_mes = {
            mes: {nome: total_orc_por_mes.get(mes, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for mes in meses_unicos
        }

        orcamentos_tri = {
            tri: {nome: total_orc_por_tri.get(tri, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for tri in trimestres_unicos
        }

        orcamentos_ano = {
            str(ano): {nome: total_orc_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dfc}
            for ano in anos_unicos
        }

        orcamento_total = {nome: total_geral_orc.get(nome, 0.0) for nome, _ in contas_dfc}
        valores_totais = {nome: total_geral_real.get(nome, 0.0) for nome, _ in contas_dfc}
        orcamentos_totais = {nome: total_geral_orc.get(nome, 0.0) for nome, _ in contas_dfc}

        def get_classificacoes(dfc_n2_name):
            sub_df = df_real[df_real["DFC_n2"] == dfc_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                total_class = grupo["valor"].sum()
                
                # Calcular valores por período
                valores_mensais = {}
                orcamentos_mensais = {}
                for mes in meses_unicos:
                    real_mes = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["mes_ano"] == mes)]["valor"].sum()
                    orc_mes = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["mes_ano"] == mes)]["valor"].sum()
                    valores_mensais[mes] = real_mes
                    orcamentos_mensais[mes] = orc_mes
                
                valores_trimestrais = {}
                orcamentos_trimestrais = {}
                for tri in trimestres_unicos:
                    real_tri = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["trimestre"] == tri)]["valor"].sum()
                    orc_tri = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["trimestre"] == tri)]["valor"].sum()
                    valores_trimestrais[tri] = real_tri
                    orcamentos_trimestrais[tri] = orc_tri
                
                valores_anuais = {}
                orcamentos_anuais = {}
                for ano in anos_unicos:
                    real_ano = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["ano"] == ano)]["valor"].sum()
                    orc_ano = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["ano"] == ano)]["valor"].sum()
                    valores_anuais[str(ano)] = real_ano
                    orcamentos_anuais[str(ano)] = orc_ano
                
                classificacoes.append({
                    "nome": classificacao,
                    "valor": total_class,
                    "valores_mensais": valores_mensais,
                    "valores_trimestrais": valores_trimestrais,
                    "valores_anuais": valores_anuais,
                    "orcamentos_mensais": orcamentos_mensais,
                    "orcamentos_trimestrais": orcamentos_trimestrais,
                    "orcamentos_anuais": orcamentos_anuais,
                    "orcamento_total": sum(orcamentos_mensais.values()),
                    "vertical_total": calcular_analise_vertical(total_class, total_geral_real.get("Recebimentos Operacionais", 0)),
                    # Adicionar campos obrigatórios para compatibilidade com frontend
                    "vertical_mensais": {mes: "–" for mes in meses_unicos},
                    "vertical_trimestrais": {tri: "–" for tri in trimestres_unicos},
                    "vertical_anuais": {str(ano): "–" for ano in anos_unicos},
                    "horizontal_mensais": {mes: "–" for mes in meses_unicos},
                    "horizontal_trimestrais": {tri: "–" for tri in trimestres_unicos},
                    "horizontal_anuais": {str(ano): "–" for ano in anos_unicos},
                    "vertical_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
                    "vertical_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
                    "vertical_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
                    "vertical_orcamentos_total": "–",
                    "horizontal_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
                    "horizontal_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
                    "horizontal_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
                    "real_vs_orcamento_mensais": {mes: "–" for mes in meses_unicos},
                    "real_vs_orcamento_trimestrais": {tri: "–" for tri in trimestres_unicos},
                    "real_vs_orcamento_anuais": {str(ano): "–" for ano in anos_unicos},
                    "real_vs_orcamento_total": "–"
                })
            return classificacoes

        def calcular_totalizadores(valores_dict):
            operacional = (
                valores_dict["Recebimentos Operacionais"] + valores_dict["Tributos sobre vendas"] + valores_dict["Custos"] + valores_dict["Desembolsos Operacionais"]
                + valores_dict["Despesas Administrativa"] + valores_dict["Despesas com Pessoal"]
                + valores_dict["Despesas com E-commerce"] + valores_dict["Despesas com Comercial"] + valores_dict["Despesas com Viagem"]
                + valores_dict["Despesas com Ocupação"] + valores_dict["Adiantamentos entrada"]
                + valores_dict["Adiantamentos saída"] + valores_dict["Impostos"]
            )
            investimento = (
                valores_dict["Investimento Comercial"] + valores_dict["Investimento em Desenvolvimento"]
                + valores_dict["Imobilizado"] + valores_dict["Intangível"] + valores_dict["Marcas e Patentes"]
            )
            financiamento = (
                valores_dict["Recebimento de Empréstimos"] + valores_dict["Receitas não operacionais"] + valores_dict["Despesas não operacionais"]
                + valores_dict["Pagamento de Empréstimos"] + valores_dict["Parcelamentos de Impostos"] + valores_dict["Aporte de capital"]
                + valores_dict["Distribuição de lucro"] + valores_dict["Aplicação Automática"] + valores_dict["Resgate Automático"]
            )
            movimentacao = (
                valores_dict["Transferência Entrada"] + valores_dict["Transferência Saída"] + valores_dict["Empréstimo de Mútuo - Crédito"] + valores_dict["Empréstimo de Mútuo - Débito"]
            )
            return operacional, investimento, financiamento, movimentacao

        def criar_linha_conta(nome, tipo, totalizador_nome):
            valores_mes = {mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos}
            valores_tri = {tri: round(valores_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
            valores_ano = {str(ano): round(valores_anuais[str(ano)][nome], 0) for ano in anos_unicos}
            orcamentos_mes = {mes: round(orcamentos_mensais[mes][nome], 0) for mes in meses_unicos}
            orcamentos_tri = {tri: round(orcamentos_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
            orcamentos_ano = {str(ano): round(orcamentos_anuais[str(ano)][nome], 0) for ano in anos_unicos}

            valores_total = valores_totais[nome]
            orcamento_total_item = orcamentos_totais[nome]

            # Análises
            real_vs_orcamento_mensais = {mes: calcular_realizado_vs_orcado(valores_mes[mes], orcamentos_mes[mes]) for mes in meses_unicos}
            real_vs_orcamento_trimestrais = {tri: calcular_realizado_vs_orcado(valores_tri[tri], orcamentos_tri[tri]) for tri in trimestres_unicos}
            real_vs_orcamento_anuais = {str(ano): calcular_realizado_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)]) for ano in anos_unicos}
            real_vs_orcamento_total = calcular_realizado_vs_orcado(valores_total, orcamento_total_item)

            # Horizontal
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

            # Vertical (baseado no totalizador)
            vertical_mensais = {}
            for mes in meses_unicos:
                base_vertical = totalizadores_mensais[mes][totalizador_nome]
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], base_vertical)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                base_vertical = totalizadores_trimestrais[tri][totalizador_nome]
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], base_vertical)

            vertical_anuais = {}
            for ano in anos_unicos:
                base_vertical = totalizadores_anuais[ano][totalizador_nome]
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], base_vertical)

            vertical_total = calcular_analise_vertical(valores_total, totalizadores_totais[totalizador_nome])

            # Orçamento análises
            vertical_orcamentos_mensais = {}
            for mes in meses_unicos:
                base_vertical = totalizadores_orc_mensais[mes][totalizador_nome]
                vertical_orcamentos_mensais[mes] = calcular_analise_vertical(orcamentos_mes[mes], base_vertical)

            vertical_orcamentos_trimestrais = {}
            for tri in trimestres_unicos:
                base_vertical = totalizadores_orc_trimestrais[tri][totalizador_nome]
                vertical_orcamentos_trimestrais[tri] = calcular_analise_vertical(orcamentos_tri[tri], base_vertical)

            vertical_orcamentos_anuais = {}
            for ano in anos_unicos:
                base_vertical = totalizadores_orc_anuais[ano][totalizador_nome]
                vertical_orcamentos_anuais[str(ano)] = calcular_analise_vertical(orcamentos_ano[str(ano)], base_vertical)

            vertical_orcamentos_total = calcular_analise_vertical(orcamento_total_item, totalizadores_orc_totais[totalizador_nome])

            # Horizontal orçamento
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
                "orcamento_total": orcamento_total_item,
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
            orcamento_total_calc = round(func(orcamentos_totais), 0)

            # Análises básicas
            real_vs_orcamento_mensais = {mes: calcular_realizado_vs_orcado(valores_mes[mes], orcamentos_mes[mes]) for mes in meses_unicos}
            real_vs_orcamento_trimestrais = {tri: calcular_realizado_vs_orcado(valores_tri[tri], orcamentos_tri[tri]) for tri in trimestres_unicos}
            real_vs_orcamento_anuais = {str(ano): calcular_realizado_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)]) for ano in anos_unicos}
            real_vs_orcamento_total = calcular_realizado_vs_orcado(total, orcamento_total_calc)

            # Horizontal
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

            # Vertical (totalizadores não têm vertical)
            vertical_mensais = {mes: "–" for mes in meses_unicos}
            vertical_trimestrais = {tri: "–" for tri in trimestres_unicos}
            vertical_anuais = {str(ano): "–" for ano in anos_unicos}
            vertical_total = "–"

            # Orçamento análises
            vertical_orcamentos_mensais = {mes: "–" for mes in meses_unicos}
            vertical_orcamentos_trimestrais = {tri: "–" for tri in trimestres_unicos}
            vertical_orcamentos_anuais = {str(ano): "–" for ano in anos_unicos}
            vertical_orcamentos_total = "–"

            # Horizontal orçamento
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
                "orcamento_total": orcamento_total_calc,
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
                "real_vs_orcamento_total": real_vs_orcamento_total
            }
        
        # Calcular totalizadores para todos os períodos
        totalizadores_mensais = {}
        for mes in meses_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_mensais[mes])
            totalizadores_mensais[mes] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        totalizadores_trimestrais = {}
        for tri in trimestres_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_trimestrais[tri])
            totalizadores_trimestrais[tri] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        totalizadores_anuais = {}
        for ano in anos_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_anuais[str(ano)])
            totalizadores_anuais[ano] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        # Totalizadores para orçamentos
        totalizadores_orc_mensais = {}
        for mes in meses_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_mensais[mes])
            totalizadores_orc_mensais[mes] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        totalizadores_orc_trimestrais = {}
        for tri in trimestres_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_trimestrais[tri])
            totalizadores_orc_trimestrais[tri] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        totalizadores_orc_anuais = {}
        for ano in anos_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_anuais[str(ano)])
            totalizadores_orc_anuais[ano] = {"Operacional": op, "Investimento": inv, "Financiamento": fin, "Movimentação entre Contas": mov}

        # Totalizador geral
        op_total, inv_total, fin_total, mov_total = calcular_totalizadores(valores_totais)
        totalizadores_totais = {
            "Operacional": op_total, "Investimento": inv_total, 
            "Financiamento": fin_total, "Movimentação entre Contas": mov_total
        }

        op_orc_total, inv_orc_total, fin_orc_total, mov_orc_total = calcular_totalizadores(orcamentos_totais)
        totalizadores_orc_totais = {
            "Operacional": op_orc_total, "Investimento": inv_orc_total, 
            "Financiamento": fin_orc_total, "Movimentação entre Contas": mov_orc_total
        }

        # Função para criar um totalizador com suas contas filhas
        def criar_totalizador(nome_totalizador, nomes_contas, func_calculo):
            # Criar o totalizador
            totalizador = calcular_linha(nome_totalizador, func_calculo)
            
            # Adicionar as contas filhas como classificações
            classificacoes = []
            for nome_conta in nomes_contas:
                conta_info = next((conta for conta in contas_dfc if conta[0] == nome_conta), None)
                if conta_info:
                    nome, tipo = conta_info
                    conta = criar_linha_conta(nome, tipo, nome_totalizador)
                    classificacoes.append(conta)
            
            totalizador["classificacoes"] = classificacoes
            return totalizador

        # Criar estrutura hierárquica

        # Primeiro criar os 4 totalizadores atuais (nível 1)
        # 1. OPERACIONAL
        operacional = criar_totalizador(
            "Operacional",
            ["Recebimentos Operacionais", "Tributos sobre vendas", "Custos", "Desembolsos Operacionais", 
             "Despesas Administrativa", "Despesas com Pessoal", "Despesas com E-commerce", "Despesas com Comercial", 
             "Despesas com Viagem", "Despesas com Ocupação", "Adiantamentos entrada", "Adiantamentos saída", "Impostos"],
            lambda v: (
                v["Recebimentos Operacionais"] + v["Tributos sobre vendas"] + v["Custos"] + v["Desembolsos Operacionais"]
                + v["Despesas Administrativa"] + v["Despesas com Pessoal"]
                + v["Despesas com E-commerce"] + v["Despesas com Comercial"] + v["Despesas com Viagem"]
                + v["Despesas com Ocupação"] + v["Adiantamentos entrada"]
                + v["Adiantamentos saída"] + v["Impostos"]
            )
        )

        # 2. INVESTIMENTO
        investimento = criar_totalizador(
            "Investimento",
            ["Investimento Comercial", "Investimento em Desenvolvimento", "Imobilizado", "Intangível", "Marcas e Patentes"],
            lambda v: (
                v["Investimento Comercial"] + v["Investimento em Desenvolvimento"]
                + v["Imobilizado"] + v["Intangível"] + v["Marcas e Patentes"]
            )
        )

        # 3. FINANCIAMENTO
        financiamento = criar_totalizador(
            "Financiamento",
            ["Recebimento de Empréstimos", "Receitas não operacionais", "Despesas não operacionais", "Pagamento de Empréstimos", 
             "Parcelamentos de Impostos", "Aporte de capital", "Distribuição de lucro", "Aplicação Automática", "Resgate Automático"],
            lambda v: (
                v["Recebimento de Empréstimos"] + v["Receitas não operacionais"] + v["Despesas não operacionais"] 
                + v["Pagamento de Empréstimos"] + v["Parcelamentos de Impostos"] + v["Aporte de capital"] 
                + v["Distribuição de lucro"] + v["Aplicação Automática"] + v["Resgate Automático"]
            )
        )

        # 4. MOVIMENTAÇÃO ENTRE CONTAS
        movimentacao_entre_contas = criar_totalizador(
            "Movimentação entre Contas",
            ["Transferência Entrada", "Transferência Saída", "Empréstimo de Mútuo - Crédito", "Empréstimo de Mútuo - Débito"],
            lambda v: (
                v["Transferência Entrada"] + v["Transferência Saída"] + v["Empréstimo de Mútuo - Crédito"] + v["Empréstimo de Mútuo - Débito"]
            )
        )

        # Função para criar um item de nível 0 (saldo inicial, movimentações, saldo final)
        def criar_item_nivel_0(nome, tipo="="):
            return {
                "tipo": tipo,
                "nome": nome,
                "valor": 0,  # Placeholder
                "valores_mensais": {mes: 0 for mes in meses_unicos},
                "valores_trimestrais": {tri: 0 for tri in trimestres_unicos},
                "valores_anuais": {str(ano): 0 for ano in anos_unicos},
                "orcamentos_mensais": {mes: 0 for mes in meses_unicos},
                "orcamentos_trimestrais": {tri: 0 for tri in trimestres_unicos},
                "orcamentos_anuais": {str(ano): 0 for ano in anos_unicos},
                "orcamento_total": 0,
                "vertical_mensais": {mes: "–" for mes in meses_unicos},
                "vertical_trimestrais": {tri: "–" for tri in trimestres_unicos},
                "vertical_anuais": {str(ano): "–" for ano in anos_unicos},
                "vertical_total": "–",
                "horizontal_mensais": {mes: "–" for mes in meses_unicos},
                "horizontal_trimestrais": {tri: "–" for tri in trimestres_unicos},
                "horizontal_anuais": {str(ano): "–" for ano in anos_unicos},
                "vertical_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
                "vertical_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
                "vertical_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
                "vertical_orcamentos_total": "–",
                "horizontal_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
                "horizontal_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
                "horizontal_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
                "real_vs_orcamento_mensais": {mes: "–" for mes in meses_unicos},
                "real_vs_orcamento_trimestrais": {tri: "–" for tri in trimestres_unicos},
                "real_vs_orcamento_anuais": {str(ano): "–" for ano in anos_unicos},
                "real_vs_orcamento_total": "–",
                "classificacoes": []
            }

        # Criar estrutura do nível 0
        result = []

        # PRIMEIRO: MOVIMENTAÇÕES (contém os 4 totalizadores como filhos)
        movimentacoes = criar_item_nivel_0("Movimentações", "=")
        
        # Calcular valores de movimentações como soma dos 4 totalizadores
        for mes in meses_unicos:
            movimentacoes["valores_mensais"][mes] = (
                operacional["valores_mensais"][mes] + 
                investimento["valores_mensais"][mes] + 
                financiamento["valores_mensais"][mes] + 
                movimentacao_entre_contas["valores_mensais"][mes]
            )
        for tri in trimestres_unicos:
            movimentacoes["valores_trimestrais"][tri] = (
                operacional["valores_trimestrais"][tri] + 
                investimento["valores_trimestrais"][tri] + 
                financiamento["valores_trimestrais"][tri] + 
                movimentacao_entre_contas["valores_trimestrais"][tri]
            )
        for ano in anos_unicos:
            movimentacoes["valores_anuais"][str(ano)] = (
                operacional["valores_anuais"][str(ano)] + 
                investimento["valores_anuais"][str(ano)] + 
                financiamento["valores_anuais"][str(ano)] + 
                movimentacao_entre_contas["valores_anuais"][str(ano)]
            )
        
        # Atualizar valor total
        movimentacoes["valor"] = (
            operacional["valor"] + 
            investimento["valor"] + 
            financiamento["valor"] + 
            movimentacao_entre_contas["valor"]
        )
        
        # Calcular orçamentos de movimentações como soma dos 4 totalizadores
        for mes in meses_unicos:
            movimentacoes["orcamentos_mensais"][mes] = (
                operacional["orcamentos_mensais"][mes] + 
                investimento["orcamentos_mensais"][mes] + 
                financiamento["orcamentos_mensais"][mes] + 
                movimentacao_entre_contas["orcamentos_mensais"][mes]
            )
        for tri in trimestres_unicos:
            movimentacoes["orcamentos_trimestrais"][tri] = (
                operacional["orcamentos_trimestrais"][tri] + 
                investimento["orcamentos_trimestrais"][tri] + 
                financiamento["orcamentos_trimestrais"][tri] + 
                movimentacao_entre_contas["orcamentos_trimestrais"][tri]
            )
        for ano in anos_unicos:
            movimentacoes["orcamentos_anuais"][str(ano)] = (
                operacional["orcamentos_anuais"][str(ano)] + 
                investimento["orcamentos_anuais"][str(ano)] + 
                financiamento["orcamentos_anuais"][str(ano)] + 
                movimentacao_entre_contas["orcamentos_anuais"][str(ano)]
            )
        
        # Atualizar orçamento total
        movimentacoes["orcamento_total"] = (
            operacional["orcamento_total"] + 
            investimento["orcamento_total"] + 
            financiamento["orcamento_total"] + 
            movimentacao_entre_contas["orcamento_total"]
        )
        
        # Adicionar os 4 totalizadores como classificações de "Movimentações"
        movimentacoes["classificacoes"] = [operacional, investimento, financiamento, movimentacao_entre_contas]

        # 1. SALDO INICIAL (0 no primeiro mês, saldo final do mês anterior nos demais)
        saldo_inicial = criar_item_nivel_0("Saldo inicial", "=")
        
        # Calcular saldo inicial mês a mês (saldo final do mês anterior)
        saldo_acumulado = 0
        for mes in meses_unicos:
            saldo_inicial["valores_mensais"][mes] = saldo_acumulado
            # Atualizar saldo acumulado para o próximo mês
            saldo_acumulado += movimentacoes["valores_mensais"][mes]
        
        # Calcular saldo inicial trimestre a trimestre
        saldo_acumulado_tri = 0
        for tri in trimestres_unicos:
            saldo_inicial["valores_trimestrais"][tri] = saldo_acumulado_tri
            saldo_acumulado_tri += movimentacoes["valores_trimestrais"][tri]
        
        # Calcular saldo inicial ano a ano
        saldo_acumulado_ano = 0
        for ano in anos_unicos:
            saldo_inicial["valores_anuais"][str(ano)] = saldo_acumulado_ano
            saldo_acumulado_ano += movimentacoes["valores_anuais"][str(ano)]
        
        # Saldo inicial total permanece 0
        saldo_inicial["valor"] = 0
        
        # Fazer o mesmo para orçamentos
        saldo_acumulado_orc = 0
        for mes in meses_unicos:
            saldo_inicial["orcamentos_mensais"][mes] = saldo_acumulado_orc
            saldo_acumulado_orc += movimentacoes["orcamentos_mensais"][mes]
        
        saldo_acumulado_orc_tri = 0
        for tri in trimestres_unicos:
            saldo_inicial["orcamentos_trimestrais"][tri] = saldo_acumulado_orc_tri
            saldo_acumulado_orc_tri += movimentacoes["orcamentos_trimestrais"][tri]
        
        saldo_acumulado_orc_ano = 0
        for ano in anos_unicos:
            saldo_inicial["orcamentos_anuais"][str(ano)] = saldo_acumulado_orc_ano
            saldo_acumulado_orc_ano += movimentacoes["orcamentos_anuais"][str(ano)]
        
        saldo_inicial["orcamento_total"] = 0
        
        result.append(saldo_inicial)

        # 2. Adicionar as movimentações
        result.append(movimentacoes)

        # 3. SALDO FINAL (saldo inicial + movimentação de cada período)
        saldo_final = criar_item_nivel_0("Saldo final", "=")
        
        # Calcular saldo final mês a mês (saldo inicial + movimentação)
        for mes in meses_unicos:
            saldo_final["valores_mensais"][mes] = saldo_inicial["valores_mensais"][mes] + movimentacoes["valores_mensais"][mes]
        
        # Calcular saldo final trimestre a trimestre
        for tri in trimestres_unicos:
            saldo_final["valores_trimestrais"][tri] = saldo_inicial["valores_trimestrais"][tri] + movimentacoes["valores_trimestrais"][tri]
        
        # Calcular saldo final ano a ano
        for ano in anos_unicos:
            saldo_final["valores_anuais"][str(ano)] = saldo_inicial["valores_anuais"][str(ano)] + movimentacoes["valores_anuais"][str(ano)]
        
        # Saldo final total
        saldo_final["valor"] = movimentacoes["valor"]
        
        # Fazer o mesmo para orçamentos
        for mes in meses_unicos:
            saldo_final["orcamentos_mensais"][mes] = saldo_inicial["orcamentos_mensais"][mes] + movimentacoes["orcamentos_mensais"][mes]
        
        for tri in trimestres_unicos:
            saldo_final["orcamentos_trimestrais"][tri] = saldo_inicial["orcamentos_trimestrais"][tri] + movimentacoes["orcamentos_trimestrais"][tri]
        
        for ano in anos_unicos:
            saldo_final["orcamentos_anuais"][str(ano)] = saldo_inicial["orcamentos_anuais"][str(ano)] + movimentacoes["orcamentos_anuais"][str(ano)]
        
        saldo_final["orcamento_total"] = movimentacoes["orcamento_total"]
        
        result.append(saldo_final)

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
        return {"error": f"Erro ao processar a DFC: {str(e)}"}
