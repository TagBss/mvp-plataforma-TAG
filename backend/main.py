import os
import time
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from financial_utils import (
    calcular_analise_vertical, calcular_analise_horizontal, 
    calcular_realizado_vs_orcado, calcular_totalizadores,
    processar_periodos_financeiros, calcular_valores_por_periodo,
    agregar_por_periodo_superior, calcular_analises_completas,
    formatar_item_financeiro
)


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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://dashboard-nextjs-and-fastapi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API está funcionando!"}

@app.get("/chart-data")
def get_chart_data():
    filename = "upload.xlsx" if os.path.exists("upload.xlsx") else "dados.xlsx"
    try:
        df = pd.read_excel(filename)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": f"Erro ao ler o arquivo: {str(e)}"}

@app.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        return {"error": "Somente arquivos .xlsx são permitidos."}
    try:
        with open("upload.xlsx", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "status": "uploaded"}
    except Exception as e:
        return {"error": f"Erro ao salvar o arquivo: {str(e)}"}

@app.get("/dre")
def get_dre_data():


    filename = "financial-data-roriz.xlsx"

    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

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
            soma_real, soma_orc = {}, {}
            for mes in meses_do_tri:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_tri[tri] = soma_real
            total_orc_por_tri[tri] = soma_orc

        total_real_por_ano = {}
        total_orc_por_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma_real, soma_orc = {}, {}
            for mes in meses_do_ano:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_ano[ano] = soma_real
            total_orc_por_ano[ano] = soma_orc

        total_geral_real = {}
        total_geral_orc = {}
        for mes in meses_unicos:
            if mes in total_real_por_mes:
                for k, v in total_real_por_mes[mes].items():
                    total_geral_real[k] = total_geral_real.get(k, 0) + v
            if mes in total_orc_por_mes:
                for k, v in total_orc_por_mes[mes].items():
                    total_geral_orc[k] = total_geral_orc.get(k, 0) + v

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

        import math

        def get_classificacoes(dre_n2_name):
            sub_df = df_real[df_real["DRE_n2"] == dre_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                grupo_validos = grupo.dropna(subset=["valor_original"])
                total = grupo_validos["valor_original"].sum()

                valores_mensais = grupo_validos.groupby("mes_ano")["valor_original"].sum().to_dict()
                valores_mensais_completos = {mes: round(valores_mensais.get(mes, 0.0), 0) for mes in meses_unicos}

                valores_trimestrais = grupo_validos.groupby("trimestre")["valor_original"].sum().to_dict()
                valores_trimestrais_completos = {tri: round(valores_trimestrais.get(tri, 0.0), 0) for tri in trimestres_unicos}

                valores_anuais = grupo_validos.groupby("ano")["valor_original"].sum().to_dict()
                valores_anuais_completos = {str(ano): round(valores_anuais.get(ano, 0.0), 0) for ano in anos_unicos}

                # orçamentos para classificações - CORRIGIDO
                grupo_orc = df[(df["DRE_n2"] == dre_n2_name) & (df["origem"] == "ORC")]
                grupo_orc = grupo_orc[grupo_orc["classificacao"] == classificacao]
                grupo_orc_validos = grupo_orc.dropna(subset=["valor_original"])

                orcamentos_mensais_class = grupo_orc_validos.groupby("mes_ano")["valor"].sum().to_dict()
                orcamentos_mensais_completos = {mes: round(orcamentos_mensais_class.get(mes, 0.0), 0) for mes in meses_unicos}

                orcamentos_trimestrais_class = grupo_orc_validos.groupby("trimestre")["valor"].sum().to_dict()
                orcamentos_trimestrais_completos = {tri: round(orcamentos_trimestrais_class.get(tri, 0.0), 0) for tri in trimestres_unicos}

                orcamentos_anuais_class = grupo_orc_validos.groupby("ano")["valor"].sum().to_dict()
                orcamentos_anuais_completos = {str(ano): round(orcamentos_anuais_class.get(ano, 0.0), 0) for ano in anos_unicos}

                # Real vs Orçamento - ADICIONADO
                real_vs_orcamento_mensais = {}
                for mes in meses_unicos:
                    real_vs_orcamento_mensais[mes] = calcular_realizado_vs_orcado(
                        valores_mensais_completos[mes], orcamentos_mensais_completos[mes]
                    )

                real_vs_orcamento_trimestrais = {}
                for tri in trimestres_unicos:
                    real_vs_orcamento_trimestrais[tri] = calcular_realizado_vs_orcado(
                        valores_trimestrais_completos[tri], orcamentos_trimestrais_completos[tri]
                    )

                real_vs_orcamento_anuais = {}
                for ano in anos_unicos:
                    real_vs_orcamento_anuais[str(ano)] = calcular_realizado_vs_orcado(
                        valores_anuais_completos[str(ano)], orcamentos_anuais_completos[str(ano)]
                    )

                real_vs_orcamento_total = calcular_realizado_vs_orcado(total, sum(orcamentos_mensais_completos.values()))

                # Análise Horizontal - CORRIGIDO
                horizontal_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        mes_anterior = meses_unicos[i - 1]
                        horizontal_mensais[mes] = calcular_analise_horizontal(
                            valores_mensais_completos[mes], valores_mensais_completos[mes_anterior]
                        )
                    else:
                        horizontal_mensais[mes] = "–"

                horizontal_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        tri_anterior = trimestres_unicos[i - 1]
                        horizontal_trimestrais[tri] = calcular_analise_horizontal(
                            valores_trimestrais_completos[tri], valores_trimestrais_completos[tri_anterior]
                        )
                    else:
                        horizontal_trimestrais[tri] = "–"

                horizontal_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                            valores_anuais_completos[str(ano)], valores_anuais_completos[str(ano_anterior)]
                        )
                    else:
                        horizontal_anuais[str(ano)] = "–"

                # Horizontal Orçamento - ADICIONADO
                horizontal_orc_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        horizontal_orc_mensais[mes] = calcular_analise_horizontal(
                            orcamentos_mensais_completos[mes], orcamentos_mensais_completos[meses_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_mensais[mes] = "–"

                horizontal_orc_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        horizontal_orc_trimestrais[tri] = calcular_analise_horizontal(
                            orcamentos_trimestrais_completos[tri], orcamentos_trimestrais_completos[trimestres_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_trimestrais[tri] = "–"

                horizontal_orc_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_orc_anuais[str(ano)] = calcular_analise_horizontal(
                            orcamentos_anuais_completos[str(ano)], orcamentos_anuais_completos[str(anos_unicos[i - 1])]
                        )
                    else:
                        horizontal_orc_anuais[str(ano)] = "–"

                classificacoes.append({
                    "tipo": "+" if total >= 0 else "-",  # Define tipo baseado no valor
                    "nome": classificacao,
                    "valor": round(total, 2),
                    "valores_mensais": valores_mensais_completos,
                    "valores_trimestrais": valores_trimestrais_completos,
                    "valores_anuais": valores_anuais_completos,
                    "orcamentos_mensais": orcamentos_mensais_completos,
                    "orcamentos_trimestrais": orcamentos_trimestrais_completos,
                    "orcamentos_anuais": orcamentos_anuais_completos,
                    "orcamento_total": round(sum(orcamentos_mensais_completos.values()), 2),
                    "vertical_mensais": {},  # Será calculado depois
                    "vertical_trimestrais": {},  # Será calculado depois
                    "vertical_anuais": {},  # Será calculado depois
                    "vertical_total": "–",  # Será calculado depois
                    "horizontal_mensais": horizontal_mensais,
                    "horizontal_trimestrais": horizontal_trimestrais,
                    "horizontal_anuais": horizontal_anuais,
                    "vertical_orcamentos_mensais": {},  # Será calculado depois
                    "vertical_orcamentos_trimestrais": {},  # Será calculado depois
                    "vertical_orcamentos_anuais": {},  # Será calculado depois
                    "vertical_orcamentos_total": "–",  # Será calculado depois
                    "horizontal_orcamentos_mensais": horizontal_orc_mensais,
                    "horizontal_orcamentos_trimestrais": horizontal_orc_trimestrais,
                    "horizontal_orcamentos_anuais": horizontal_orc_anuais,
                    "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                    "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                    "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                    "real_vs_orcamento_total": real_vs_orcamento_total,
                    "classificacoes": []  # Nível 3 não tem filhos
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
                if i > 0:
                    horizontal_mensais[mes] = calcular_analise_horizontal(valores_mes[mes], valores_mes[meses_unicos[i - 1]])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_tri[tri], valores_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_ano[str(ano)], valores_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_anuais[str(ano)] = "–"

            ### Vertical Realizado
            vertical_mensais = {}
            for mes in meses_unicos:
                receita_mes = valores_mensais[mes]["Faturamento"]
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], receita_mes)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                receita_tri = valores_trimestrais[tri]["Faturamento"]
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], receita_tri)

            vertical_anuais = {}
            for ano in anos_unicos:
                receita_ano = valores_anuais[str(ano)]["Faturamento"]
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], receita_ano)

            vertical_total = calcular_analise_vertical(valores_total, valores_totais["Faturamento"])

            ### Vertical Orçamento
            vertical_orcamentos_mensais = {}
            for mes in meses_unicos:
                receita_mes_orc = orcamentos_mensais[mes]["Faturamento"]
                vertical_orcamentos_mensais[mes] = calcular_analise_vertical(orcamentos_mes[mes], receita_mes_orc)

            vertical_orcamentos_trimestrais = {}
            for tri in trimestres_unicos:
                receita_tri_orc = orcamentos_trimestrais[tri]["Faturamento"]
                vertical_orcamentos_trimestrais[tri] = calcular_analise_vertical(orcamentos_tri[tri], receita_tri_orc)

            vertical_orcamentos_anuais = {}
            for ano in anos_unicos:
                receita_ano_orc = orcamentos_anuais[str(ano)]["Faturamento"]
                vertical_orcamentos_anuais[str(ano)] = calcular_analise_vertical(orcamentos_ano[str(ano)], receita_ano_orc)

            vertical_orcamentos_total = calcular_analise_vertical(orcamento_total, orcamentos_totais["Faturamento"])

            ### Horizontal Orçamento
            horizontal_orcamentos_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i - 1]])
                else:
                    horizontal_orcamentos_mensais[mes] = "–"

            horizontal_orcamentos_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_orcamentos_trimestrais[tri] = "–"

            horizontal_orcamentos_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_orcamentos_anuais[str(ano)] = "–"

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
                "classificacoes": []  # Nível 3 não tem filhos
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
                if i > 0:
                    mes_anterior = meses_unicos[i - 1]
                    horizontal_mensais[mes] = calcular_analise_horizontal(valores_mes[mes], valores_mes[mes_anterior])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    tri_anterior = trimestres_unicos[i - 1]
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_tri[tri], valores_tri[tri_anterior])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    ano_anterior = anos_unicos[i - 1]
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_ano[str(ano)], valores_ano[str(ano_anterior)])
                else:
                    horizontal_anuais[str(ano)] = "–"

            # Análise Vertical - CORRIGIDO
            vertical_mensais = {}
            for mes in meses_unicos:
                receita_mes = valores_mensais[mes]["Faturamento"]
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], receita_mes)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                receita_tri = valores_trimestrais[tri]["Faturamento"]
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], receita_tri)

            vertical_anuais = {}
            for ano in anos_unicos:
                receita_ano = valores_anuais[str(ano)]["Faturamento"]
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], receita_ano)

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
                if i > 0:
                    horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i - 1]])
                else:
                    horizontal_orcamentos_mensais[mes] = "–"

            horizontal_orcamentos_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_orcamentos_trimestrais[tri] = "–"

            horizontal_orcamentos_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_orcamentos_anuais[str(ano)] = "–"

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
                "real_vs_orcamento_total": real_vs_orcamento_total
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
                    classificacao["vertical_mensais"] = {}
                    classificacao["vertical_trimestrais"] = {}
                    classificacao["vertical_anuais"] = {}

                    for mes in meses_unicos:
                        base_valor = valores_mensais[mes]["Faturamento"]
                        filho_valor = classificacao["valores_mensais"][mes]
                        classificacao["vertical_mensais"][mes] = calcular_analise_vertical(filho_valor, base_valor)

                    for tri in trimestres_unicos:
                        base_valor = valores_trimestrais[tri]["Faturamento"]
                        filho_valor = classificacao["valores_trimestrais"][tri]
                        classificacao["vertical_trimestrais"][tri] = calcular_analise_vertical(filho_valor, base_valor)

                    for ano in anos_unicos:
                        base_valor = valores_anuais[str(ano)]["Faturamento"]
                        filho_valor = classificacao["valores_anuais"][str(ano)]
                        classificacao["vertical_anuais"][str(ano)] = calcular_analise_vertical(filho_valor, base_valor)

                    classificacao["vertical_total"] = calcular_analise_vertical(
                        classificacao["valor"],
                        valores_totais["Faturamento"]
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
    
@app.get("/dfc")
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
            soma_real, soma_orc = {}, {}
            for mes in meses_do_tri:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_tri[tri] = soma_real
            total_orc_por_tri[tri] = soma_orc

        total_real_por_ano = {}
        total_orc_por_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma_real, soma_orc = {}, {}
            for mes in meses_do_ano:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_ano[ano] = soma_real
            total_orc_por_ano[ano] = soma_orc

        total_geral_real = {}
        total_geral_orc = {}
        for mes in meses_unicos:
            if mes in total_real_por_mes:
                for k, v in total_real_por_mes[mes].items():
                    total_geral_real[k] = total_geral_real.get(k, 0) + v
            if mes in total_orc_por_mes:
                for k, v in total_orc_por_mes[mes].items():
                    total_geral_orc[k] = total_geral_orc.get(k, 0) + v

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

        import math

        def get_classificacoes(dfc_n2_name):
            sub_df = df_real[df_real["DFC_n2"] == dfc_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                grupo_validos = grupo.dropna(subset=["valor"])
                total = grupo_validos["valor"].sum()

                valores_mensais = grupo_validos.groupby("mes_ano")["valor"].sum().to_dict()
                valores_mensais_completos = {mes: round(valores_mensais.get(mes, 0.0), 0) for mes in meses_unicos}

                valores_trimestrais = grupo_validos.groupby("trimestre")["valor"].sum().to_dict()
                valores_trimestrais_completos = {tri: round(valores_trimestrais.get(tri, 0.0), 0) for tri in trimestres_unicos}

                valores_anuais = grupo_validos.groupby("ano")["valor"].sum().to_dict()
                valores_anuais_completos = {str(ano): round(valores_anuais.get(ano, 0.0), 0) for ano in anos_unicos}

                # orçamentos para classificações - CORRIGIDO
                grupo_orc = df[(df["DFC_n2"] == dfc_n2_name) & (df["origem"] == "ORC")]
                grupo_orc = grupo_orc[grupo_orc["classificacao"] == classificacao]
                grupo_orc_validos = grupo_orc.dropna(subset=["valor"])

                orcamentos_mensais_class = grupo_orc_validos.groupby("mes_ano")["valor"].sum().to_dict()
                orcamentos_mensais_completos = {mes: round(orcamentos_mensais_class.get(mes, 0.0), 0) for mes in meses_unicos}

                orcamentos_trimestrais_class = grupo_orc_validos.groupby("trimestre")["valor"].sum().to_dict()
                orcamentos_trimestrais_completos = {tri: round(orcamentos_trimestrais_class.get(tri, 0.0), 0) for tri in trimestres_unicos}

                orcamentos_anuais_class = grupo_orc_validos.groupby("ano")["valor"].sum().to_dict()
                orcamentos_anuais_completos = {str(ano): round(orcamentos_anuais_class.get(ano, 0.0), 0) for ano in anos_unicos}

                # Real vs Orçamento - ADICIONADO
                real_vs_orcamento_mensais = {}
                for mes in meses_unicos:
                    real_vs_orcamento_mensais[mes] = calcular_realizado_vs_orcado(
                        valores_mensais_completos[mes], orcamentos_mensais_completos[mes]
                    )

                real_vs_orcamento_trimestrais = {}
                for tri in trimestres_unicos:
                    real_vs_orcamento_trimestrais[tri] = calcular_realizado_vs_orcado(
                        valores_trimestrais_completos[tri], orcamentos_trimestrais_completos[tri]
                    )

                real_vs_orcamento_anuais = {}
                for ano in anos_unicos:
                    real_vs_orcamento_anuais[str(ano)] = calcular_realizado_vs_orcado(
                        valores_anuais_completos[str(ano)], orcamentos_anuais_completos[str(ano)]
                    )

                real_vs_orcamento_total = calcular_realizado_vs_orcado(total, sum(orcamentos_mensais_completos.values()))

                # Análise Horizontal - CORRIGIDO
                horizontal_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        mes_anterior = meses_unicos[i - 1]
                        horizontal_mensais[mes] = calcular_analise_horizontal(
                            valores_mensais_completos[mes], valores_mensais_completos[mes_anterior]
                        )
                    else:
                        horizontal_mensais[mes] = "–"

                horizontal_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        tri_anterior = trimestres_unicos[i - 1]
                        horizontal_trimestrais[tri] = calcular_analise_horizontal(
                            valores_trimestrais_completos[tri], valores_trimestrais_completos[tri_anterior]
                        )
                    else:
                        horizontal_trimestrais[tri] = "–"

                horizontal_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                            valores_anuais_completos[str(ano)], valores_anuais_completos[str(ano_anterior)]
                        )
                    else:
                        horizontal_anuais[str(ano)] = "–"

                # Horizontal Orçamento - ADICIONADO
                horizontal_orc_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        horizontal_orc_mensais[mes] = calcular_analise_horizontal(
                            orcamentos_mensais_completos[mes], orcamentos_mensais_completos[meses_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_mensais[mes] = "–"

                horizontal_orc_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        horizontal_orc_trimestrais[tri] = calcular_analise_horizontal(
                            orcamentos_trimestrais_completos[tri], orcamentos_trimestrais_completos[trimestres_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_trimestrais[tri] = "–"

                horizontal_orc_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        horizontal_orc_anuais[str(ano)] = calcular_analise_horizontal(
                            orcamentos_anuais_completos[str(ano)], orcamentos_anuais_completos[str(anos_unicos[i - 1])]
                        )
                    else:
                        horizontal_orc_anuais[str(ano)] = "–"

                classificacoes.append({
                    "tipo": "+" if total >= 0 else "-",  # Define tipo baseado no valor
                    "nome": classificacao,
                    "valor": round(total, 2),
                    "valores_mensais": valores_mensais_completos,
                    "valores_trimestrais": valores_trimestrais_completos,
                    "valores_anuais": valores_anuais_completos,
                    "orcamentos_mensais": orcamentos_mensais_completos,
                    "orcamentos_trimestrais": orcamentos_trimestrais_completos,
                    "orcamentos_anuais": orcamentos_anuais_completos,
                    "orcamento_total": round(sum(orcamentos_mensais_completos.values()), 2),
                    "vertical_mensais": {},  # Será calculado depois
                    "vertical_trimestrais": {},  # Será calculado depois
                    "vertical_anuais": {},  # Será calculado depois
                    "vertical_total": "–",  # Será calculado depois
                    "horizontal_mensais": horizontal_mensais,
                    "horizontal_trimestrais": horizontal_trimestrais,
                    "horizontal_anuais": horizontal_anuais,
                    "vertical_orcamentos_mensais": {},  # Será calculado depois
                    "vertical_orcamentos_trimestrais": {},  # Será calculado depois
                    "vertical_orcamentos_anuais": {},  # Será calculado depois
                    "vertical_orcamentos_total": "–",  # Será calculado depois
                    "horizontal_orcamentos_mensais": horizontal_orc_mensais,
                    "horizontal_orcamentos_trimestrais": horizontal_orc_trimestrais,
                    "horizontal_orcamentos_anuais": horizontal_orc_anuais,
                    "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                    "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                    "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                    "real_vs_orcamento_total": real_vs_orcamento_total,
                    "classificacoes": []  # Nível 3 não tem filhos
                })
            return classificacoes

        def calcular_totalizadores(valores_dict):
            """Calcula os totalizadores que serão usados como base para análise vertical"""
            operacional = (
                valores_dict["Recebimentos Operacionais"] + valores_dict["Tributos sobre vendas"] + 
                valores_dict["Custos"] + valores_dict["Desembolsos Operacionais"] +
                valores_dict["Despesas Administrativa"] + valores_dict["Despesas com Pessoal"] +
                valores_dict["Despesas com E-commerce"] + valores_dict["Despesas com Comercial"] + 
                valores_dict["Despesas com Viagem"] + valores_dict["Despesas com Ocupação"] + 
                valores_dict["Adiantamentos entrada"] + valores_dict["Adiantamentos saída"] + 
                valores_dict["Impostos"]
            )
            
            investimento = (
                valores_dict["Investimento Comercial"] + valores_dict["Investimento em Desenvolvimento"] +
                valores_dict["Imobilizado"] + valores_dict["Intangível"] + valores_dict["Marcas e Patentes"]
            )
            
            financiamento = (
                valores_dict["Recebimento de Empréstimos"] + valores_dict["Receitas não operacionais"] + 
                valores_dict["Despesas não operacionais"] + valores_dict["Pagamento de Empréstimos"] + 
                valores_dict["Parcelamentos de Impostos"] + valores_dict["Aporte de capital"] + 
                valores_dict["Distribuição de lucro"] + valores_dict["Aplicação Automática"] + 
                valores_dict["Resgate Automático"]
            )
            
            movimentacao = (
                valores_dict["Transferência Entrada"] + valores_dict["Transferência Saída"] + 
                valores_dict["Empréstimo de Mútuo - Crédito"] + valores_dict["Empréstimo de Mútuo - Débito"]
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
            orcamento_total = orcamentos_totais[nome]

            ### Real vs Orçado
            real_vs_orcamento_mensais = {mes: calcular_realizado_vs_orcado(valores_mes[mes], orcamentos_mes[mes]) for mes in meses_unicos}
            real_vs_orcamento_trimestrais = {tri: calcular_realizado_vs_orcado(valores_tri[tri], orcamentos_tri[tri]) for tri in trimestres_unicos}
            real_vs_orcamento_anuais = {str(ano): calcular_realizado_vs_orcado(valores_ano[str(ano)], orcamentos_ano[str(ano)]) for ano in anos_unicos}
            real_vs_orcamento_total = calcular_realizado_vs_orcado(valores_total, orcamento_total)

            ### Horizontal Realizado
            horizontal_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    horizontal_mensais[mes] = calcular_analise_horizontal(valores_mes[mes], valores_mes[meses_unicos[i - 1]])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_tri[tri], valores_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_ano[str(ano)], valores_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_anuais[str(ano)] = "–"

            ### Vertical Realizado - usando totalizador correto!
            vertical_mensais = {}
            for mes in meses_unicos:
                base = totalizadores_mensais[mes][totalizador_nome]
                vertical_mensais[mes] = calcular_analise_vertical(valores_mes[mes], base)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                base = totalizadores_trimestrais[tri][totalizador_nome]
                vertical_trimestrais[tri] = calcular_analise_vertical(valores_tri[tri], base)

            vertical_anuais = {}
            for ano in anos_unicos:
                base = totalizadores_anuais[str(ano)][totalizador_nome]
                vertical_anuais[str(ano)] = calcular_analise_vertical(valores_ano[str(ano)], base)

            vertical_total = calcular_analise_vertical(valores_total, totalizadores_totais[totalizador_nome])

            ### Vertical Orçamento - usando totalizador correto!
            vertical_orcamentos_mensais = {}
            for mes in meses_unicos:
                base = totalizadores_orc_mensais[mes][totalizador_nome]
                vertical_orcamentos_mensais[mes] = calcular_analise_vertical(orcamentos_mes[mes], base)

            vertical_orcamentos_trimestrais = {}
            for tri in trimestres_unicos:
                base = totalizadores_orc_trimestrais[tri][totalizador_nome]
                vertical_orcamentos_trimestrais[tri] = calcular_analise_vertical(orcamentos_tri[tri], base)

            vertical_orcamentos_anuais = {}
            for ano in anos_unicos:
                base = totalizadores_orc_anuais[str(ano)][totalizador_nome]
                vertical_orcamentos_anuais[str(ano)] = calcular_analise_vertical(orcamentos_ano[str(ano)], base)

            vertical_orcamentos_total = calcular_analise_vertical(orcamento_total, totalizadores_orc_totais[totalizador_nome])

            ### Horizontal Orçamento
            horizontal_orcamentos_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i - 1]])
                else:
                    horizontal_orcamentos_mensais[mes] = "–"

            horizontal_orcamentos_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_orcamentos_trimestrais[tri] = "–"

            horizontal_orcamentos_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_orcamentos_anuais[str(ano)] = "–"

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
                if i > 0:
                    mes_anterior = meses_unicos[i - 1]
                    horizontal_mensais[mes] = calcular_analise_horizontal(valores_mes[mes], valores_mes[mes_anterior])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    tri_anterior = trimestres_unicos[i - 1]
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_tri[tri], valores_tri[tri_anterior])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    ano_anterior = anos_unicos[i - 1]
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_ano[str(ano)], valores_ano[str(ano_anterior)])
                else:
                    horizontal_anuais[str(ano)] = "–"

            # Análise Vertical - CORRIGIDO
            vertical_mensais = {}
            vertical_trimestrais = {}
            vertical_anuais = {}
            vertical_total = "–"  # Totalizadores não têm análise vertical

            # Horizontal Orçamento
            horizontal_orcamentos_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    horizontal_orcamentos_mensais[mes] = calcular_analise_horizontal(orcamentos_mes[mes], orcamentos_mes[meses_unicos[i - 1]])
                else:
                    horizontal_orcamentos_mensais[mes] = "–"

            horizontal_orcamentos_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    horizontal_orcamentos_trimestrais[tri] = calcular_analise_horizontal(orcamentos_tri[tri], orcamentos_tri[trimestres_unicos[i - 1]])
                else:
                    horizontal_orcamentos_trimestrais[tri] = "–"

            horizontal_orcamentos_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    horizontal_orcamentos_anuais[str(ano)] = calcular_analise_horizontal(orcamentos_ano[str(ano)], orcamentos_ano[str(anos_unicos[i - 1])])
                else:
                    horizontal_orcamentos_anuais[str(ano)] = "–"

            # Vertical Orçamento
            vertical_orcamentos_mensais = {}
            vertical_orcamentos_trimestrais = {}
            vertical_orcamentos_anuais = {}
            vertical_orcamentos_total = "–"  # Totalizadores não têm análise vertical

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
                "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                "real_vs_orcamento_total": real_vs_orcamento_total
            }
        
        # Calcular totalizadores para todos os períodos
        totalizadores_mensais = {}
        for mes in meses_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_mensais[mes])
            totalizadores_mensais[mes] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

        totalizadores_trimestrais = {}
        for tri in trimestres_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_trimestrais[tri])
            totalizadores_trimestrais[tri] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

        totalizadores_anuais = {}
        for ano in anos_unicos:
            op, inv, fin, mov = calcular_totalizadores(valores_anuais[str(ano)])
            totalizadores_anuais[str(ano)] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

        # Totalizadores para orçamentos
        totalizadores_orc_mensais = {}
        for mes in meses_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_mensais[mes])
            totalizadores_orc_mensais[mes] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

        totalizadores_orc_trimestrais = {}
        for tri in trimestres_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_trimestrais[tri])
            totalizadores_orc_trimestrais[tri] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

        totalizadores_orc_anuais = {}
        for ano in anos_unicos:
            op, inv, fin, mov = calcular_totalizadores(orcamentos_anuais[str(ano)])
            totalizadores_orc_anuais[str(ano)] = {
                "Operacional": op, "Investimento": inv, 
                "Financiamento": fin, "Movimentação entre Contas": mov
            }

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
            # Criar todas as contas filhas
            contas_filhas = []
            for nome_conta in nomes_contas:
                tipo = "+" if any(palavra in nome_conta for palavra in ["Recebimentos", "entrada", "Receitas", "Aporte", "Resgate", "Crédito"]) else "-"
                conta = criar_linha_conta(nome_conta, tipo, nome_totalizador)
                
                # Calcular análise vertical para as classificações desta conta
                if "classificacoes" in conta and conta["classificacoes"]:
                    for classificacao in conta["classificacoes"]:
                        classificacao["vertical_mensais"] = {}
                        classificacao["vertical_trimestrais"] = {}
                        classificacao["vertical_anuais"] = {}

                        for mes in meses_unicos:
                            base_valor = totalizadores_mensais[mes][nome_totalizador]
                            filho_valor = classificacao["valores_mensais"][mes]
                            classificacao["vertical_mensais"][mes] = calcular_analise_vertical(filho_valor, base_valor)

                        for tri in trimestres_unicos:
                            base_valor = totalizadores_trimestrais[tri][nome_totalizador]
                            filho_valor = classificacao["valores_trimestrais"][tri]
                            classificacao["vertical_trimestrais"][tri] = calcular_analise_vertical(filho_valor, base_valor)

                        for ano in anos_unicos:
                            base_valor = totalizadores_anuais[str(ano)][nome_totalizador]
                            filho_valor = classificacao["valores_anuais"][str(ano)]
                            classificacao["vertical_anuais"][str(ano)] = calcular_analise_vertical(filho_valor, base_valor)

                        classificacao["vertical_total"] = calcular_analise_vertical(
                            classificacao["valor"],
                            totalizadores_totais[nome_totalizador]
                        )
                
                contas_filhas.append(conta)
            
            # Criar o totalizador principal
            totalizador = calcular_linha(nome_totalizador, func_calculo)
            totalizador["classificacoes"] = contas_filhas
            
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
            valores_mes = {}
            valores_tri = {}
            valores_ano = {}
            
            # Para saldo inicial e final, buscar dados do endpoint saldos-evolucao
            if nome in ["Saldo inicial", "Saldo final"]:
                try:
                    saldos_evolucao = get_saldos_evolucao()
                    if saldos_evolucao.get("success"):
                        evolucao_data = saldos_evolucao["data"]["evolucao"]
                        for item in evolucao_data:
                            mes = item["mes"]
                            if nome == "Saldo inicial":
                                valores_mes[mes] = round(item["saldo_inicial"], 0)
                            else:  # Saldo final
                                valores_mes[mes] = round(item["saldo_final"], 0)
                        
                        # Agregar por trimestre e ano
                        for tri in trimestres_unicos:
                            ano_tri = tri.split('-T')[0]
                            trimestre_num = tri.split('-T')[1]
                            if trimestre_num == '1':
                                meses_do_tri = [m for m in meses_unicos if m.startswith(ano_tri) and m.split('-')[1] in ['01', '02', '03']]
                            elif trimestre_num == '2':
                                meses_do_tri = [m for m in meses_unicos if m.startswith(ano_tri) and m.split('-')[1] in ['04', '05', '06']]
                            elif trimestre_num == '3':
                                meses_do_tri = [m for m in meses_unicos if m.startswith(ano_tri) and m.split('-')[1] in ['07', '08', '09']]
                            else:  # T4
                                meses_do_tri = [m for m in meses_unicos if m.startswith(ano_tri) and m.split('-')[1] in ['10', '11', '12']]
                            
                            if meses_do_tri:
                                if nome == "Saldo inicial":
                                    valores_tri[tri] = valores_mes.get(min(meses_do_tri), 0)
                                else:  # Saldo final
                                    valores_tri[tri] = valores_mes.get(max(meses_do_tri), 0)
                        
                        for ano in anos_unicos:
                            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
                            if meses_do_ano:
                                if nome == "Saldo inicial":
                                    valores_ano[str(ano)] = valores_mes.get(min(meses_do_ano), 0)
                                else:  # Saldo final
                                    valores_ano[str(ano)] = valores_mes.get(max(meses_do_ano), 0)
                    else:
                        # Se falhou, usar valores zero
                        for mes in meses_unicos:
                            valores_mes[mes] = 0
                        for tri in trimestres_unicos:
                            valores_tri[tri] = 0
                        for ano in anos_unicos:
                            valores_ano[str(ano)] = 0
                except:
                    # Se falhou, usar valores zero
                    for mes in meses_unicos:
                        valores_mes[mes] = 0
                    for tri in trimestres_unicos:
                        valores_tri[tri] = 0
                    for ano in anos_unicos:
                        valores_ano[str(ano)] = 0
            else:
                # Para movimentações, inicializar com zero (será calculado depois)
                for mes in meses_unicos:
                    valores_mes[mes] = 0
                for tri in trimestres_unicos:
                    valores_tri[tri] = 0
                for ano in anos_unicos:
                    valores_ano[str(ano)] = 0

            valor_total = sum(valores_mes.values()) if valores_mes else 0

            # Para saldos, orçamentos são zero (não faz sentido orçar saldo inicial/final)
            orcamentos_mes = {mes: 0 for mes in meses_unicos}
            orcamentos_tri = {tri: 0 for tri in trimestres_unicos}
            orcamentos_ano = {str(ano): 0 for ano in anos_unicos}
            orcamento_total = 0

            # Análises horizontais e verticais (simplificadas para nível 0)
            horizontal_mensais = {mes: "–" for mes in meses_unicos}
            horizontal_trimestrais = {tri: "–" for tri in trimestres_unicos}
            horizontal_anuais = {str(ano): "–" for ano in anos_unicos}
            
            vertical_mensais = {mes: "–" for mes in meses_unicos}
            vertical_trimestrais = {tri: "–" for tri in trimestres_unicos}
            vertical_anuais = {str(ano): "–" for ano in anos_unicos}
            vertical_total = "–"

            real_vs_orcamento_mensais = {mes: "–" for mes in meses_unicos}
            real_vs_orcamento_trimestrais = {tri: "–" for tri in trimestres_unicos}
            real_vs_orcamento_anuais = {str(ano): "–" for ano in anos_unicos}
            real_vs_orcamento_total = "–"

            return {
                "tipo": tipo,
                "nome": nome,
                "valor": valor_total,
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
                "vertical_orcamentos_mensais": vertical_mensais,
                "vertical_orcamentos_trimestrais": vertical_trimestrais,
                "vertical_orcamentos_anuais": vertical_anuais,
                "vertical_orcamentos_total": vertical_total,
                "horizontal_orcamentos_mensais": horizontal_mensais,
                "horizontal_orcamentos_trimestrais": horizontal_trimestrais,
                "horizontal_orcamentos_anuais": horizontal_anuais,
                "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                "real_vs_orcamento_total": real_vs_orcamento_total,
                "classificacoes": []
            }

        # Criar estrutura do nível 0
        result = []

        # 1. SALDO INICIAL
        saldo_inicial = criar_item_nivel_0("Saldo inicial", "=")
        result.append(saldo_inicial)

        # 2. MOVIMENTAÇÕES (contém os 4 totalizadores como filhos)
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
        result.append(movimentacoes)

        # 3. SALDO FINAL
        saldo_final = criar_item_nivel_0("Saldo final", "=")
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
            soma_real, soma_orc = {}, {}
            for mes in meses_do_tri:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_tri[tri] = soma_real
            total_orc_por_tri[tri] = soma_orc

        total_real_por_ano = {}
        total_orc_por_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma_real, soma_orc = {}, {}
            for mes in meses_do_ano:
                for k, v in total_real_por_mes.get(mes, {}).items():
                    soma_real[k] = soma_real.get(k, 0) + v
                for k, v in total_orc_por_mes.get(mes, {}).items():
                    soma_orc[k] = soma_orc.get(k, 0) + v
            total_real_por_ano[ano] = soma_real
            total_orc_por_ano[ano] = soma_orc

        total_geral_real = {}
        total_geral_orc = {}
        for mes in meses_unicos:
            if mes in total_real_por_mes:
                for k, v in total_real_por_mes[mes].items():
                    total_geral_real[k] = total_geral_real.get(k, 0) + v
            if mes in total_orc_por_mes:
                for k, v in total_orc_por_mes[mes].items():
                    total_geral_orc[k] = total_geral_orc.get(k, 0) + v

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

        import math

        def get_classificacoes(dfc_n2_name):
            sub_df = df_real[df_real["DFC_n2"] == dfc_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                grupo_validos = grupo.dropna(subset=["valor"])
                total = grupo_validos["valor"].sum()

                valores_mensais = grupo_validos.groupby("mes_ano")["valor"].sum().to_dict()
                valores_mensais_completos = {mes: round(valores_mensais.get(mes, 0.0), 0) for mes in meses_unicos}

                valores_trimestrais = grupo_validos.groupby("trimestre")["valor"].sum().to_dict()
                valores_trimestrais_completos = {tri: round(valores_trimestrais.get(tri, 0.0), 0) for tri in trimestres_unicos}

                valores_anuais = grupo_validos.groupby("ano")["valor"].sum().to_dict()
                valores_anuais_completos = {str(ano): round(valores_anuais.get(ano, 0.0), 0) for ano in anos_unicos}

                # orçamentos para classificações - CORRIGIDO
                grupo_orc = df[(df["DFC_n2"] == dfc_n2_name) & (df["origem"] == "ORC")]
                grupo_orc = grupo_orc[grupo_orc["classificacao"] == classificacao]
                grupo_orc_validos = grupo_orc.dropna(subset=["valor"])

                orcamentos_mensais_class = grupo_orc_validos.groupby("mes_ano")["valor"].sum().to_dict()
                orcamentos_mensais_completos = {mes: round(orcamentos_mensais_class.get(mes, 0.0), 0) for mes in meses_unicos}

                orcamentos_trimestrais_class = grupo_orc_validos.groupby("trimestre")["valor"].sum().to_dict()
                orcamentos_trimestrais_completos = {tri: round(orcamentos_trimestrais_class.get(tri, 0.0), 0) for tri in trimestres_unicos}

                orcamentos_anuais_class = grupo_orc_validos.groupby("ano")["valor"].sum().to_dict()
                orcamentos_anuais_completos = {str(ano): round(orcamentos_anuais_class.get(ano, 0.0), 0) for ano in anos_unicos}

                # Real vs Orçamento - ADICIONADO
                real_vs_orcamento_mensais = {}
                for mes in meses_unicos:
                    real_vs_orcamento_mensais[mes] = calcular_realizado_vs_orcado(
                        valores_mensais_completos[mes], orcamentos_mensais_completos[mes]
                    )

                real_vs_orcamento_trimestrais = {}
                for tri in trimestres_unicos:
                    real_vs_orcamento_trimestrais[tri] = calcular_realizado_vs_orcado(
                        valores_trimestrais_completos[tri], orcamentos_trimestrais_completos[tri]
                    )

                real_vs_orcamento_anuais = {}
                for ano in anos_unicos:
                    real_vs_orcamento_anuais[str(ano)] = calcular_realizado_vs_orcado(
                        valores_anuais_completos[str(ano)], orcamentos_anuais_completos[str(ano)]
                    )

                real_vs_orcamento_total = calcular_realizado_vs_orcado(total, sum(orcamentos_mensais_completos.values()))

                # Análise Horizontal - CORRIGIDO
                horizontal_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        mes_anterior = meses_unicos[i - 1]
                        horizontal_mensais[mes] = calcular_analise_horizontal(
                            valores_mensais_completos[mes], valores_mensais_completos[mes_anterior]
                        )
                    else:
                        horizontal_mensais[mes] = "–"

                horizontal_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        tri_anterior = trimestres_unicos[i - 1]
                        horizontal_trimestrais[tri] = calcular_analise_horizontal(
                            valores_trimestrais_completos[tri], valores_trimestrais_completos[tri_anterior]
                        )
                    else:
                        horizontal_trimestrais[tri] = "–"

                horizontal_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                            valores_anuais_completos[str(ano)], valores_anuais_completos[str(ano_anterior)]
                        )
                    else:
                        horizontal_anuais[str(ano)] = "–"

                # Horizontal Orçamento - ADICIONADO
                horizontal_orc_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        horizontal_orc_mensais[mes] = calcular_analise_horizontal(
                            orcamentos_mensais_completos[mes], orcamentos_mensais_completos[meses_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_mensais[mes] = "–"

                horizontal_orc_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        horizontal_orc_trimestrais[tri] = calcular_analise_horizontal(
                            orcamentos_trimestrais_completos[tri], orcamentos_trimestrais_completos[trimestres_unicos[i - 1]]
                        )
                    else:
                        horizontal_orc_trimestrais[tri] = "–"

                horizontal_orc_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_orc_anuais[str(ano)] = calcular_analise_horizontal(
                            orcamentos_anuais_completos[str(ano)], orcamentos_anuais_completos[str(anos_unicos[i - 1])]
                        )
                    else:
                        horizontal_orc_anuais[str(ano)] = "–"

                classificacoes.append({
                    "tipo": "+" if total >= 0 else "-",  # Define tipo baseado no valor
                    "nome": classificacao,
                    "valor": round(total, 2),
                    "valores_mensais": valores_mensais_completos,
                    "valores_trimestrais": valores_trimestrais_completos,
                    "valores_anuais": valores_anuais_completos,
                    "orcamentos_mensais": orcamentos_mensais_completos,
                    "orcamentos_trimestrais": orcamentos_trimestrais_completos,
                    "orcamentos_anuais": orcamentos_anuais_completos,
                    "orcamento_total": round(sum(orcamentos_mensais_completos.values()), 2),
                    "vertical_mensais": {},  # Será calculado depois
                    "vertical_trimestrais": {},  # Será calculado depois
                    "vertical_anuais": {},  # Será calculado depois
                    "vertical_total": "–",  # Será calculado depois
                    "horizontal_mensais": horizontal_mensais,
                    "horizontal_trimestrais": horizontal_trimestrais,
                    "horizontal_anuais": horizontal_anuais,
                    "vertical_orcamentos_mensais": {},  # Será calculado depois
                    "vertical_orcamentos_trimestrais": {},  # Será calculado depois
                    "vertical_orcamentos_anuais": {},  # Será calculado depois
                    "vertical_orcamentos_total": "–",  # Será calculado depois
                    "horizontal_orcamentos_mensais": horizontal_orc_mensais,
                    "horizontal_orcamentos_trimestrais": horizontal_orc_trimestrais,
                    "horizontal_orcamentos_anuais": horizontal_orc_anuais,
                    "real_vs_orcamento_mensais": real_vs_orcamento_mensais,
                    "real_vs_orcamento_trimestrais": real_vs_orcamento_trimestrais,
                    "real_vs_orcamento_anuais": real_vs_orcamento_anuais,
                    "real_vs_orcamento_total": real_vs_orcamento_total,
                    "classificacoes": []  # Nível 3 não tem filhos
                })
            return classificacoes

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
                    classificacao["vertical_mensais"] = {}
                    classificacao["vertical_trimestrais"] = {}
                    classificacao["vertical_anuais"] = {}

                    for mes in meses_unicos:
                        base_valor = valores_mensais[mes]["Faturamento"]
                        filho_valor = classificacao["valores_mensais"][mes]
                        classificacao["vertical_mensais"][mes] = calcular_analise_vertical(filho_valor, base_valor)

                    for tri in trimestres_unicos:
                        base_valor = valores_trimestrais[tri]["Faturamento"]
                        filho_valor = classificacao["valores_trimestrais"][tri]
                        classificacao["vertical_trimestrais"][tri] = calcular_analise_vertical(filho_valor, base_valor)

                    for ano in anos_unicos:
                        base_valor = valores_anuais[str(ano)]["Faturamento"]
                        filho_valor = classificacao["valores_anuais"][str(ano)]
                        classificacao["vertical_anuais"][str(ano)] = calcular_analise_vertical(filho_valor, base_valor)

                    classificacao["vertical_total"] = calcular_analise_vertical(
                        classificacao["valor"],
                        valores_totais["Faturamento"]
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
        return {"error": f"Erro ao processar a DFC: {str(e)}"}

def calcular_mom(df_filtrado, date_column, origem):
    """
    Calcula variação Month over Month (MoM)
    """
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

def calcular_saldo(origem: str, mes_filtro: str = None):
    """
    Calcula saldo genérico baseado na origem:
    - Se origem == 'CAR': Contas a Receber
    - Se origem == 'CAP': Contas a Pagar
    """
    filename = "financial-data-roriz.xlsx"
    
    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Validação das colunas obrigatórias
        required_columns = ["valor", "origem", "DFC_n1"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        # Identificar coluna de data
        date_column = next((col for col in df.columns if col.lower() == "data"), None)
        if not date_column:
            return {"error": "Coluna de data não encontrada"}

        # Processar dados
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

        df = df.dropna(subset=[date_column, "valor"])

        # Filtrar apenas contas diferentes de DFC_n1 "Movimentação entre Contas"
        df_con = df[
            (df["DFC_n1"] != "Movimentação entre Contas") & 
            (df["DFC_n1"].notna())
        ].copy()

        # Filtrar pela origem dinâmica para MoM (NÃO filtra por mês)
        df_mom = df_con[df_con["origem"] == origem].copy()

        # Calcular MoM SEM filtro de mês (sempre retorna todos os meses)
        mom_data = calcular_mom(df_mom, date_column, origem)

        # Filtrar pela origem dinâmica para saldo (pode filtrar por mês)
        df_filtrado = df_con[df_con["origem"] == origem].copy()
        if mes_filtro:
            df_filtrado = df_filtrado[
                df_filtrado[date_column].dt.strftime("%Y-%m") == mes_filtro
            ]

        if df_filtrado.empty:
            return {
                "error": f"Não foram encontrados registros com origem '{origem}'",
                "total_passado": 0,
                "total_futuro": 0,
                "saldo_total": 0,
                "anos_disponiveis": [],
                "meses_disponiveis": []
            }

        hoje = pd.Timestamp.now().normalize()

        # Soma dos valores
        total_passado = df_filtrado[df_filtrado[date_column] < hoje]["valor"].sum()
        total_futuro = df_filtrado[df_filtrado[date_column] >= hoje]["valor"].sum()
        saldo_total = total_passado + total_futuro

        total_registros = len(df_filtrado)
        registros_passados = len(df_filtrado[df_filtrado[date_column] < hoje])
        registros_futuros = len(df_filtrado[df_filtrado[date_column] >= hoje])

        # Anos e meses disponíveis
        if not mes_filtro:
            # Se for todo o período, pegue todos os meses/anos disponíveis do df_con (toda a origem)
            anos_disponiveis = sorted(df_con[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_con[date_column].dt.strftime("%Y-%m").unique().tolist())
        else:
            anos_disponiveis = sorted(df_filtrado[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_filtrado[date_column].dt.strftime("%Y-%m").unique().tolist())

        # Calcular PMR (Prazo Médio de Recebimento)
        # data_caixa = se data existe, usa data, senão usa vencimento
        data_caixa_col = None
        if "data" in df_con.columns and "vencimento" in df_con.columns:
            data_caixa_col = df_con["data"].combine_first(df_con["vencimento"])
        elif "data" in df_con.columns:
            data_caixa_col = df_con["data"]
        elif "vencimento" in df_con.columns:
            data_caixa_col = df_con["vencimento"]

        pmr = None
        pmp = None
        # Calcular PMR (Prazo Médio de Recebimento)
        if origem == "CAR" and data_caixa_col is not None and "competencia" in df_con.columns:
            mask = (
                df_con["origem"] == "CAR"
                ) & (
                (df_con["DFC_n2"].fillna("") == "Recebimentos Operacionais")
                ) & (
                data_caixa_col.notna()
                ) & (
                df_con["competencia"].notna()
                )
            df_pmr = df_con[mask].copy()
            if not df_pmr.empty:
                data_caixa = pd.to_datetime(data_caixa_col[mask], errors="coerce")
                competencia = pd.to_datetime(df_pmr["competencia"], errors="coerce")
                dias = (data_caixa - competencia).dt.days
                ponderado = (dias * df_pmr["valor"]).sum()
                soma_pesos = df_pmr["valor"].sum()
                if soma_pesos != 0:
                    pmr = round(ponderado / soma_pesos, 0)

        # Calcular PMP (Prazo Médio de Pagamento)
        if origem == "CAP" and data_caixa_col is not None and "competencia" in df_con.columns:
            mask = (
                df_con["origem"] == "CAP"
                ) & (
                (df_con["DFC_n1"].fillna("") != "Movimentação entre Contas")
                ) & (
                data_caixa_col.notna()
                ) & (
                df_con["competencia"].notna()
                )
            df_pmp = df_con[mask].copy()
            if not df_pmp.empty:
                data_caixa = pd.to_datetime(data_caixa_col[mask], errors="coerce")
                competencia = pd.to_datetime(df_pmp["competencia"], errors="coerce")
                dias = (data_caixa - competencia).dt.days
                ponderado = (dias * df_pmp["valor"]).sum()
                soma_pesos = df_pmp["valor"].sum()
                if soma_pesos != 0:
                    pmp = round(ponderado / soma_pesos, 0)

        return {
            "success": True,
            "data": {
                "total_passado": round(total_passado, 2),
                "total_futuro": round(total_futuro, 2),
                "saldo_total": round(saldo_total, 2),
                "data_calculo": hoje.strftime("%Y-%m-%d"),
                "estatisticas": {
                    "total_registros": total_registros,
                    "registros_passados": registros_passados,
                    "registros_futuros": registros_futuros
                },
                "anos_disponiveis": anos_disponiveis,
                "meses_disponiveis": meses_disponiveis,
                "mom_analysis": mom_data,
                "pmr": f"{int(pmr)} dias" if pmr is not None else None,
                "pmp": f"{int(pmp)} dias" if pmp is not None else None
            }
        }
        
    except Exception as e:
        return {"error": f"Erro ao calcular saldo: {str(e)}"}

@app.get("/receber")
def get_caixa_saldo(mes: str = None):
    return calcular_saldo("CAR", mes)

@app.get("/pagar")
def get_pagar_saldo(mes: str = None):
    return calcular_saldo("CAP", mes)

# Novo cálculo e endpoint para movimentações (CAP + CAR)
@app.get("/movimentacoes")
def get_movimentacoes(mes: str = None):
    """
    Retorna a soma dos saldos de CAP e CAR, incluindo saldo_total, mom_analysis e meses_disponiveis.
    """
    try:
        # Calcula CAP e CAR separadamente
        cap = calcular_saldo("CAP", mes)
        car = calcular_saldo("CAR", mes)

        # Se algum dos dois retornou erro, retorna erro
        if not cap.get("success") or not car.get("success"):
            return {"error": "Erro ao calcular movimentações", "cap": cap, "car": car}

        # Soma os saldos
        saldo_total = (cap["data"].get("saldo_total", 0) or 0) + (car["data"].get("saldo_total", 0) or 0)
        total_passado = (cap["data"].get("total_passado", 0) or 0) + (car["data"].get("total_passado", 0) or 0)
        total_futuro = (cap["data"].get("total_futuro", 0) or 0) + (car["data"].get("total_futuro", 0) or 0)

        # Unir meses disponíveis
        meses_disponiveis = sorted(list(set(cap["data"].get("meses_disponiveis", [])) | set(car["data"].get("meses_disponiveis", []))))
        anos_disponiveis = sorted(list(set(cap["data"].get("anos_disponiveis", [])) | set(car["data"].get("anos_disponiveis", []))))

        # Unir mom_analysis por mês (soma dos valores de cada mês)
        mom_cap = {item["mes"]: item for item in cap["data"].get("mom_analysis", [])}
        mom_car = {item["mes"]: item for item in car["data"].get("mom_analysis", [])}
        all_meses = sorted(set(mom_cap.keys()) | set(mom_car.keys()))
        mom_analysis = []
        for mes in all_meses:
            valor_atual = (mom_cap.get(mes, {}).get("valor_atual", 0) or 0) + (mom_car.get(mes, {}).get("valor_atual", 0) or 0)
            valor_anterior = (mom_cap.get(mes, {}).get("valor_anterior", 0) or 0) + (mom_car.get(mes, {}).get("valor_anterior", 0) or 0)
            variacao_absoluta = None
            variacao_percentual = None
            if valor_anterior != 0:
                variacao_absoluta = round((valor_atual - valor_anterior), 2)
                variacao_percentual = round((valor_atual - valor_anterior) / valor_anterior * 100, 2)
            mom_analysis.append({
                "mes": mes,
                "valor_atual": round(valor_atual, 2),
                "valor_anterior": round(valor_anterior, 2) if valor_anterior != 0 else None,
                "variacao_absoluta": round(variacao_absoluta, 2) if variacao_absoluta != 0 else None,
                "variacao_percentual": variacao_percentual
            })

        return {
            "success": True,
            "data": {
                "saldo_total": round(saldo_total, 2),
                "total_passado": round(total_passado, 2),
                "total_futuro": round(total_futuro, 2),
                "meses_disponiveis": meses_disponiveis,
                "anos_disponiveis": anos_disponiveis,
                "mom_analysis": mom_analysis
            }
        }
    except Exception as e:
        return {"error": f"Erro ao calcular movimentações: {str(e)}"}

# Novo endpoint para evolução de saldos (saldo inicial, movimentação, saldo final)
@app.get("/saldos-evolucao")
def get_saldos_evolucao():
    """
    Retorna a evolução de saldos mês a mês: saldo inicial, movimentação (CAP + CAR), saldo final.
    O saldo inicial do primeiro mês é zero, saldo final = saldo inicial + movimentação.
    O saldo inicial do mês seguinte é o saldo final do mês anterior.
    """
    try:
        cap = calcular_saldo("CAP")
        car = calcular_saldo("CAR")
        if not cap.get("success") or not car.get("success"):
            return {"error": "Erro ao calcular movimentações", "cap": cap, "car": car}

        mom_cap = {item["mes"]: item for item in cap["data"].get("mom_analysis", [])}
        mom_car = {item["mes"]: item for item in car["data"].get("mom_analysis", [])}
        all_meses = sorted(set(mom_cap.keys()) | set(mom_car.keys()))

        evolucao = []
        saldo_inicial = 0.0
        for idx, mes in enumerate(all_meses):
            movimentacao = (mom_cap.get(mes, {}).get("valor_atual", 0) or 0) + (mom_car.get(mes, {}).get("valor_atual", 0) or 0)
            saldo_final = round(saldo_inicial + movimentacao, 2)
            # Calcular MoM para saldo_final
            variacao_absoluta = None
            variacao_percentual = None
            if idx > 0:
                saldo_final_anterior = evolucao[idx-1]["saldo_final"]
                variacao_absoluta = round(saldo_final - saldo_final_anterior, 2)
                if saldo_final_anterior != 0:
                    variacao_percentual = round((saldo_final - saldo_final_anterior) / saldo_final_anterior * 100, 2)
            evolucao.append({
                "mes": mes,
                "saldo_inicial": round(saldo_inicial, 2),
                "movimentacao": round(movimentacao, 2),
                "saldo_final": saldo_final,
                "variacao_absoluta": variacao_absoluta,
                "variacao_percentual": variacao_percentual
            })
            saldo_inicial = saldo_final

        return {
            "success": True,
            "data": {
                "evolucao": evolucao,
                "meses_disponiveis": all_meses
            }
        }
    except Exception as e:
        return {"error": f"Erro ao calcular evolução de saldos: {str(e)}"}

# Endpoint para custos agrupados por classificação mês a mês e total geral
@app.get("/custos-visao-financeiro")
def get_custos():
    filename = "financial-data-roriz.xlsx"
    df = get_cached_df(filename)
    if df is None:
        return {"error": "Erro ao ler o arquivo Excel."}

    # Validação das colunas obrigatórias
    required_columns = ["valor", "DFC_n2", "classificacao"]
    if not all(col in df.columns for col in required_columns):
        return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

    # Filtrar apenas custos e origem CAR ou CAP
    if "origem" not in df.columns:
        return {"error": "A planilha deve conter a coluna 'origem'"}
    df_custos = df[(df["DFC_n2"] == "Custos") & (df["origem"].isin(["CAR", "CAP"]))].copy()
    if df_custos.empty:
        return {"error": "Não há dados de custos na planilha para origem 'CAR' ou 'CAP'."}

    # Identificar coluna de data
    date_column = next((col for col in df_custos.columns if col.lower() == "data"), None)
    if not date_column:
        return {"error": "Coluna de data não encontrada"}

    df_custos[date_column] = pd.to_datetime(df_custos[date_column], errors="coerce")
    df_custos = df_custos.dropna(subset=[date_column, "valor"])
    df_custos["mes_ano"] = df_custos[date_column].dt.to_period("M").astype(str)

    # Custos por classificação mês a mês
    custos_mes_class = (
        df_custos.groupby(["classificacao", "mes_ano"])['valor'].sum().reset_index()
    )

    # Estruturar resposta: { classificacao: { mes_ano: valor, ... }, ... }
    resultado = {}
    for _, row in custos_mes_class.iterrows():
        classificacao = row["classificacao"] or "Sem classificação"
        mes_ano = row["mes_ano"]
        valor = float(row["valor"])
        if classificacao not in resultado:
            resultado[classificacao] = {}
        resultado[classificacao][mes_ano] = valor

    # Total geral por classificação (todos os meses)
    total_geral = (
        df_custos.groupby("classificacao")['valor'].sum().to_dict()
    )
    # Converter para float
    total_geral = {k or "Sem classificação": float(v) for k, v in total_geral.items()}

    # Custos totais mês a mês (sem classificação)
    custos_mes = df_custos.groupby("mes_ano")["valor"].sum().to_dict()
    custos_mes = {k: float(v) for k, v in custos_mes.items()}

    # Total geral de custos (sem classificação)
    total_geral_custos = float(df_custos["valor"].sum())

    # Cálculo da análise MoM (Month-over-Month) dos custos totais
    # Ordenar meses cronologicamente
    meses_ordenados = sorted(custos_mes.keys())
    mom_analysis = []
    for idx, mes in enumerate(meses_ordenados):
        valor_atual = custos_mes[mes]
        valor_anterior = custos_mes[meses_ordenados[idx-1]] if idx > 0 else None
        variacao_absoluta = None
        variacao_percentual = None
        if valor_anterior is not None:
            variacao_absoluta = valor_atual - valor_anterior
            variacao_percentual = ((valor_atual - valor_anterior) / valor_anterior * 100) if valor_anterior != 0 else None
        mom_analysis.append({
            "mes": mes,
            "valor_atual": valor_atual,
            "valor_anterior": valor_anterior,
            "variacao_absoluta": variacao_absoluta,
            "variacao_percentual": variacao_percentual
        })

    return {
        "success": True,
        "data": {
            "custos_mes_classificacao": resultado,
            "total_geral_classificacao": total_geral,
            "custos_mes": custos_mes,
            "total_geral": total_geral_custos,
            "mom_analysis": mom_analysis
        }
    }