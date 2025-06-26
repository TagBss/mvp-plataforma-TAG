from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import shutil
import os
import math

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
    filename = "upload.xlsx" if os.path.exists("upload.xlsx") else "financial-data-roriz.xlsx"

    try:
        df = pd.read_excel(filename)

        required_columns = ["DRE_n2", "valor_original", "classificacao"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        # Tratar datas e valores corretamente
        date_column = next((col for col in df.columns if col.lower() == "competencia"), None)
        if date_column:
            df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
            df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
        else:
            df["mes_ano"] = None

        # Converter valor_original para numérico e preservar NaNs
        df["valor_original"] = pd.to_numeric(df["valor_original"], errors="coerce")

        # Filtrar apenas linhas com competencia válida
        df = df.dropna(subset=[date_column])

        # Lista de meses únicos baseada em competencia
        meses_unicos = sorted(df["mes_ano"].dropna().unique())

        # Gerar totais ignorando apenas linhas com valor_original nulo
        df_validos = df.dropna(subset=["valor_original"])

        total_geral = df_validos.groupby("DRE_n2")["valor_original"].sum().to_dict()

        total_por_mes = {
            mes: df_validos[df_validos["mes_ano"] == mes].groupby("DRE_n2")["valor_original"].sum().to_dict()
            for mes in meses_unicos
        }

        def get_classificacoes(dre_n2_name):
            sub_df = df[df["DRE_n2"] == dre_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                grupo_validos = grupo.dropna(subset=["valor_original"])
                total = grupo_validos["valor_original"].sum()
                valores_mensais = grupo_validos.groupby("mes_ano")["valor_original"].sum().to_dict()
                valores_mensais = {
                    mes: round(valores_mensais.get(mes, 0.0), 2) for mes in meses_unicos
                }
                classificacoes.append({
                    "nome": classificacao,
                    "valor": round(total, 2),
                    "valores_mensais": valores_mensais
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

        def criar_linha_conta(nome, tipo):
            return {
                "tipo": tipo,
                "nome": nome,
                "valor": round(valores_totais[nome], 0),
                "valores_mensais": {
                    mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos
                },
                "classificacoes": get_classificacoes(nome)
            }

        def calcular_linha(nome, func, tipo="="):
            total = round(func(valores_totais), 0)
            valores = {
                mes: round(func(valores_mensais[mes]), 0) for mes in meses_unicos
            }
            return {
                "tipo": tipo,
                "nome": nome,
                "valor": total,
                "valores_mensais": valores
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
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] -
            v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"]
        )))

        for nome in ["Depreciação", "Amortização"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("EBIT", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] -
            v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
            v["Depreciação"] - v["Amortização"]
        )))

        for nome in ["Receitas Financeiras", "Despesas Financeiras", "Receitas não operacionais", "Despesas não operacionais"]:
            result.append(criar_linha_conta(nome, "+" if "Receitas" in nome else "-"))

        result.append(calcular_linha("Resultado Financeiro", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] -
            v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
            v["Depreciação"] - v["Amortização"] + v["Receitas Financeiras"] - v["Despesas Financeiras"] +
            v["Receitas não operacionais"] - v["Despesas não operacionais"]
        )))

        for nome in ["IRPJ", "CSLL"]:
            result.append(criar_linha_conta(nome, "-"))

        result.append(calcular_linha("Resultado Líquido", lambda v: (
            v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] -
            v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
            v["Depreciação"] - v["Amortização"] + v["Receitas Financeiras"] - v["Despesas Financeiras"] +
            v["Receitas não operacionais"] - v["Despesas não operacionais"] - v["IRPJ"] - v["CSLL"]
        )))

        return {
            "meses": meses_unicos,
            "data": result
        }

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}