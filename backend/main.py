from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import shutil
import os

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
        df = pd.read_excel(filename)

        required_columns = ["DRE_n2", "valor_original", "classificacao"]
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

        total_por_mes = {
            mes: df[df["mes_ano"] == mes].groupby("DRE_n2")["valor_original"].sum().to_dict()
            for mes in meses_unicos
        }

        total_por_tri = {}
        for tri in trimestres_unicos:
            meses_do_tri = df[df["trimestre"] == tri]["mes_ano"].unique()
            soma = {}
            for mes in meses_do_tri:
                for k, v in total_por_mes[mes].items():
                    soma[k] = soma.get(k, 0) + v
            total_por_tri[tri] = soma

        total_por_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma = {}
            for mes in meses_do_ano:
                for k, v in total_por_mes[mes].items():
                    soma[k] = soma.get(k, 0) + v
            total_por_ano[ano] = soma
            print(f"Meses do ano {ano} -> {meses_do_ano}")
            print(f"Soma do ano {ano} -> {soma}")

        total_geral = {}
        for mes in meses_unicos:
            for k, v in total_por_mes[mes].items():
                total_geral[k] = total_geral.get(k, 0) + v

        print("Meses únicos:", meses_unicos)
        print("Anos únicos:", anos_unicos)
        print("Total por mês:", total_por_mes)
        print("Total por ano:", total_por_ano)

        contas_dre = [
            ("Faturamento", "+"),
            ("Tributos e deduções sobre a receita", "-"),
            ("CMV", "-"),
            ("CSP", "-"),
            ("CPV", "-"),
            ("Despesas Administrativas", "-"),
            ("Despesas com Pessoal", "-"),
            ("Despesas com Ocupação", "-"),
            ("Despesas Comerciais", "-"),
            ("Depreciação", "-"),
            ("Amortização", "-"),
            ("Receitas Financeiras", "+"),
            ("Despesas Financeiras", "-"),
            ("Receitas não operacionais", "+"),
            ("Despesas não operacionais", "-"),
            ("IRPJ", "-"),
            ("CSLL", "-")
        ]

        valores_totais = {nome: total_geral.get(nome, 0.0) for nome, _ in contas_dre}
        valores_mensais = {
            mes: {nome: total_por_mes[mes].get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }
        valores_trimestrais = {
            tri: {nome: total_por_tri[tri].get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }
        valores_anuais = {
            str(ano): {nome: total_por_ano.get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }

        print("Valores anuais corrigidos:", valores_anuais)

        import math

        def calcular_analise_vertical_por_periodo(item_valor, receita_valor):
            if receita_valor == 0 or math.isnan(receita_valor):
                return "–"
            return f"{((item_valor / receita_valor) * 100):.1f}%"

        def calcular_analise_vertical(valor, base_valor, is_pai=False):
            if is_pai:
                return "100.0%"
            if base_valor is None or base_valor == 0 or math.isnan(base_valor):
                return "–"
            return f"{((valor / base_valor) * 100):.1f}%"

        def calcular_analise_horizontal(valor_atual, valor_anterior):
            if valor_anterior is None or valor_anterior == 0 or math.isnan(valor_anterior):
                return "–"
            diff = ((valor_atual - valor_anterior) / valor_anterior) * 100
            return f"{diff:+.1f}%"

        def get_classificacoes(dre_n2_name):
            sub_df = df[df["DRE_n2"] == dre_n2_name]
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

                horizontal_mensais = {}
                for i, mes in enumerate(meses_unicos):
                    if i > 0:
                        mes_anterior = meses_unicos[i - 1]
                        horizontal_mensais[mes] = calcular_analise_horizontal(
                            valores_mensais_completos[mes],
                            valores_mensais_completos[mes_anterior]
                        )
                    else:
                        horizontal_mensais[mes] = "–"

                horizontal_trimestrais = {}
                for i, tri in enumerate(trimestres_unicos):
                    if i > 0:
                        tri_anterior = trimestres_unicos[i - 1]
                        horizontal_trimestrais[tri] = calcular_analise_horizontal(
                            valores_trimestrais_completos[tri],
                            valores_trimestrais_completos[tri_anterior]
                        )
                    else:
                        horizontal_trimestrais[tri] = "–"

                horizontal_anuais = {}
                for i, ano in enumerate(anos_unicos):
                    if i > 0:
                        ano_anterior = anos_unicos[i - 1]
                        horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                            valores_anuais_completos[str(ano)],
                            valores_anuais_completos[str(ano_anterior)]
                        )
                    else:
                        horizontal_anuais[str(ano)] = "–"

                classificacoes.append({
                    "nome": classificacao,
                    "valor": round(total, 2),
                    "valores_mensais": valores_mensais_completos,
                    "valores_trimestrais": valores_trimestrais_completos,
                    "valores_anuais": valores_anuais_completos,
                    "horizontal_mensais": horizontal_mensais,
                    "horizontal_trimestrais": horizontal_trimestrais,
                    "horizontal_anuais": horizontal_anuais
                })
            return classificacoes

        contas_dre = [
            ("Faturamento", "+"),
            ("Tributos e deduções sobre a receita", "-"),
            ("CMV", "-"),
            ("CSP", "-"),
            ("CPV", "-"),
            ("Despesas Administrativas", "-"),
            ("Despesas com Pessoal", "-"),
            ("Despesas com Ocupação", "-"),
            ("Despesas Comerciais", "-"),
            ("Depreciação", "-"),
            ("Amortização", "-"),
            ("Receitas Financeiras", "+"),
            ("Despesas Financeiras", "-"),
            ("Receitas não operacionais", "+"),
            ("Despesas não operacionais", "-"),
            ("IRPJ", "-"),
            ("CSLL", "-")
        ]

        valores_totais = {nome: total_geral.get(nome, 0.0) for nome, _ in contas_dre}
        valores_mensais = {
            mes: {nome: total_por_mes[mes].get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }
        valores_trimestrais = {
            tri: {nome: total_por_tri[tri].get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }
        valores_anuais = {
            str(ano): {nome: total_por_ano[ano].get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }

        def criar_linha_conta(nome, tipo):
            valores_mes = {mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos}
            valores_tri = {tri: round(valores_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
            valores_ano = {str(ano): round(valores_anuais[str(ano)][nome], 0) for ano in anos_unicos}

            horizontal_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    mes_anterior = meses_unicos[i - 1]
                    horizontal_mensais[mes] = calcular_analise_horizontal(
                        valores_mes[mes], valores_mes[mes_anterior])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    tri_anterior = trimestres_unicos[i - 1]
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(
                        valores_tri[tri], valores_tri[tri_anterior])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    ano_anterior = anos_unicos[i - 1]
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                        valores_ano[str(ano)], valores_ano[str(ano_anterior)])
                else:
                    horizontal_anuais[str(ano)] = "–"

            # Análise Vertical baseada no Faturamento
            vertical_mensais = {}
            for mes in meses_unicos:
                receita_mes = valores_mensais[mes]["Faturamento"]
                vertical_mensais[mes] = calcular_analise_vertical_por_periodo(valores_mes[mes], receita_mes)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                receita_tri = valores_trimestrais[tri]["Faturamento"] 
                vertical_trimestrais[tri] = calcular_analise_vertical_por_periodo(valores_tri[tri], receita_tri)

            vertical_anuais = {}
            for ano in anos_unicos:
                receita_ano = valores_anuais[str(ano)]["Faturamento"]
                vertical_anuais[str(ano)] = calcular_analise_vertical_por_periodo(valores_ano[str(ano)], receita_ano)

            receita_total = valores_totais["Faturamento"]
            vertical_total = calcular_analise_vertical_por_periodo(valores_totais[nome], receita_total)

            return {
                "tipo": tipo,
                "nome": nome,
                "valor": round(valores_totais[nome], 0),
                "valores_mensais": valores_mes,
                "valores_trimestrais": valores_tri,
                "valores_anuais": valores_ano,
                "vertical_mensais": vertical_mensais,
                "vertical_trimestrais": vertical_trimestrais,
                "vertical_anuais": vertical_anuais,
                "vertical_total": vertical_total,
                "horizontal_mensais": horizontal_mensais,
                "horizontal_trimestrais": horizontal_trimestrais,
                "horizontal_anuais": horizontal_anuais,
                "classificacoes": get_classificacoes(nome)
            }

        def calcular_linha(nome, func, tipo="="):
            total = round(func(valores_totais), 0)
            valores_mes = {mes: round(func(valores_mensais[mes]), 0) for mes in meses_unicos}
            valores_tri = {tri: round(func(valores_trimestrais[tri]), 0) for tri in trimestres_unicos}
            valores_ano = {str(ano): round(func(valores_anuais[str(ano)]), 0) for ano in anos_unicos}

            horizontal_mensais = {}
            for i, mes in enumerate(meses_unicos):
                if i > 0:
                    mes_anterior = meses_unicos[i - 1]
                    horizontal_mensais[mes] = calcular_analise_horizontal(
                        valores_mes[mes], valores_mes[mes_anterior])
                else:
                    horizontal_mensais[mes] = "–"

            horizontal_trimestrais = {}
            for i, tri in enumerate(trimestres_unicos):
                if i > 0:
                    tri_anterior = trimestres_unicos[i - 1]
                    horizontal_trimestrais[tri] = calcular_analise_horizontal(
                        valores_tri[tri], valores_tri[tri_anterior])
                else:
                    horizontal_trimestrais[tri] = "–"

            horizontal_anuais = {}
            for i, ano in enumerate(anos_unicos):
                if i > 0:
                    ano_anterior = anos_unicos[i - 1]
                    horizontal_anuais[str(ano)] = calcular_analise_horizontal(
                        valores_ano[str(ano)], valores_ano[str(ano_anterior)])
                else:
                    horizontal_anuais[str(ano)] = "–"

            # Análise Vertical baseada no Faturamento
            vertical_mensais = {}
            for mes in meses_unicos:
                receita_mes = valores_mensais[mes]["Faturamento"]
                vertical_mensais[mes] = calcular_analise_vertical_por_periodo(valores_mes[mes], receita_mes)

            vertical_trimestrais = {}
            for tri in trimestres_unicos:
                receita_tri = valores_trimestrais[tri]["Faturamento"]
                vertical_trimestrais[tri] = calcular_analise_vertical_por_periodo(valores_tri[tri], receita_tri)

            vertical_anuais = {}
            for ano in anos_unicos:
                receita_ano = valores_anuais[str(ano)]["Faturamento"]
                vertical_anuais[str(ano)] = calcular_analise_vertical_por_periodo(valores_ano[str(ano)], receita_ano)

            receita_total = valores_totais["Faturamento"]
            vertical_total = calcular_analise_vertical_por_periodo(total, receita_total)

            return {
                "tipo": tipo,
                "nome": nome,
                "valor": total,
                "valores_mensais": valores_mes,
                "valores_trimestrais": valores_tri,
                "valores_anuais": valores_ano,
                "vertical_mensais": vertical_mensais,
                "vertical_trimestrais": vertical_trimestrais,
                "vertical_anuais": vertical_anuais,
                "vertical_total": vertical_total,
                "horizontal_mensais": horizontal_mensais,
                "horizontal_trimestrais": horizontal_trimestrais,
                "horizontal_anuais": horizontal_anuais
            }

        result = []
        result.append(criar_linha_conta("Faturamento", "+"))
        result.append(calcular_linha("Receita Bruta", lambda v: v["Faturamento"]))
        result.append(criar_linha_conta("Tributos e deduções sobre a receita", "-"))
        result.append(calcular_linha("Receita Líquida", lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"]))

        for nome in ["CMV", "CSP", "CPV"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("Resultado Bruto", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]
        )))

        for nome in ["Despesas Administrativas", "Despesas com Pessoal", "Despesas com Ocupação", "Despesas Comerciais"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("EBITDA", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]
            - v["Despesas Administrativas"] - v["Despesas com Pessoal"]
            - v["Despesas com Ocupação"] - v["Despesas Comerciais"]
        )))

        for nome in ["Depreciação", "Amortização"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("EBIT", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]
            - v["Despesas Administrativas"] - v["Despesas com Pessoal"]
            - v["Despesas com Ocupação"] - v["Despesas Comerciais"]
            - v["Depreciação"] - v["Amortização"]
        )))

        for nome in ["Receitas Financeiras", "Despesas Financeiras",
                     "Receitas não operacionais", "Despesas não operacionais"]:
            result.append(criar_linha_conta(nome, "+" if "Receitas" in nome else "-"))

        result.append(calcular_linha("Resultado Financeiro", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]
            - v["Despesas Administrativas"] - v["Despesas com Pessoal"]
            - v["Despesas com Ocupação"] - v["Despesas Comerciais"]
            - v["Depreciação"] - v["Amortização"]
            + v["Receitas Financeiras"] - v["Despesas Financeiras"]
            + v["Receitas não operacionais"] - v["Despesas não operacionais"]
        )))

        for nome in ["IRPJ", "CSLL"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("Resultado Líquido", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]
            - v["Despesas Administrativas"] - v["Despesas com Pessoal"]
            - v["Despesas com Ocupação"] - v["Despesas Comerciais"]
            - v["Depreciação"] - v["Amortização"]
            + v["Receitas Financeiras"] - v["Despesas Financeiras"]
            + v["Receitas não operacionais"] - v["Despesas não operacionais"]
            - v["IRPJ"] - v["CSLL"]
        )))

        # Calcular análise vertical para as classificações
        for item in result:
            if "classificacoes" in item and item["classificacoes"]:
                for classificacao in item["classificacoes"]:
                    classificacao["vertical_mensais"] = {}
                    classificacao["vertical_trimestrais"] = {}
                    classificacao["vertical_anuais"] = {}

                    for mes in meses_unicos:
                        pai_valor = item["valores_mensais"][mes]
                        filho_valor = classificacao["valores_mensais"][mes]
                        classificacao["vertical_mensais"][mes] = calcular_analise_vertical(filho_valor, pai_valor)

                    for tri in trimestres_unicos:
                        pai_valor = item["valores_trimestrais"][tri]
                        filho_valor = classificacao["valores_trimestrais"][tri]
                        classificacao["vertical_trimestrais"][tri] = calcular_analise_vertical(filho_valor, pai_valor)

                    for ano in anos_unicos:
                        pai_valor = item["valores_anuais"][str(ano)]
                        filho_valor = classificacao["valores_anuais"][str(ano)]
                        classificacao["vertical_anuais"][str(ano)] = calcular_analise_vertical(filho_valor, pai_valor)

                    classificacao["vertical_total"] = calcular_analise_vertical(classificacao["valor"], item["valor"])

        return {
            "meses": meses_unicos,
            "trimestres": trimestres_unicos,
            "anos": anos_unicos,
            "data": result
        }

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}