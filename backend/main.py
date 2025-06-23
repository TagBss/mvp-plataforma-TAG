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
    filename = "upload.xlsx" if os.path.exists("upload.xlsx") else "financial-data-roriz.xlsx"
    try:
        df = pd.read_excel(filename)

        estrutura_dre = [
            ("+","Faturamento", "Receita Bruta"),
            ("=","Receita Bruta", None),
            ("-","Tributos e deduções sobre a receita", "Receita Líquida"),
            ("=","Receita Líquida", None),
            ("-","CMV", "Resultado Bruto"),
            ("-","CSP", "Resultado Bruto"),
            ("-","CPV", "Resultado Bruto"),
            ("=","Resultado Bruto", None),
            ("-","Despesas Administrativas", "EBITDA"),
            ("-","Despesas com Pessoal", "EBITDA"),
            ("-","Despesas com Ocupação", "EBITDA"),
            ("-","Despesas Comerciais", "EBITDA"),
            ("=","EBITDA", None),
            ("-","Depreciação", "EBIT"),
            ("-","Amortização", "EBIT"),
            ("=","EBIT", None),
            ("+","Receitas Financeiras", "Resultado Financeiro"),
            ("-","Despesas Financeiras", "Resultado Financeiro"),
            ("+ / -","Receitas / Despesas não operacionais", "Resultado Financeiro"),
            ("=","Resultado Financeiro", None),
            ("-","IRPJ", "Resultado Líquido"),
            ("-","CSLL", "Resultado Líquido"),
            ("=","Resultado Líquido", None)
        ]

        resultado = []

        for tipo, nome, agrupador in estrutura_dre:
            linhas = df[df["DRE_n2"] == nome]
            valor_total = linhas["valor_original"].sum()

            resultado.append({
                "tipo": tipo,
                "nome": nome,
                "valor": valor_total
            })

            # Adiciona as classificações detalhadas logo após o grupo
            for _, row in linhas.iterrows():
                resultado.append({
                    "tipo": tipo,
                    "nome": row["de [classificacao]"],
                    "valor": row["valor_original"]
                })

        return resultado

    except Exception as e:
        return {"error": f"Erro ao processar DRE: {str(e)}"}