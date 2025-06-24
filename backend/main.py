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
    # Define o nome do arquivo a ser lido: se o upload existir, usa ele; senão, usa o padrão
    filename = "upload.xlsx" if os.path.exists("upload.xlsx") else "financial-data-roriz.xlsx"

    try:
        # Lê o arquivo Excel
        df = pd.read_excel(filename)

        # Verifica se as colunas essenciais existem
        required_columns = ["DRE_n2", "valor_original", "classificacao"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        # Agrupa os valores por DRE_n2 (contas intermediárias), somando os valores
        dre_n2_sums = df.groupby("DRE_n2")["valor_original"].sum().to_dict()

        # Função para obter detalhes das classificações por DRE_n2
        def get_classificacoes(dre_n2_name):
            filtered_df = df[df["DRE_n2"] == dre_n2_name]
            if filtered_df.empty:
                return []
            
            # Agrupa por classificação e soma os valores
            classificacoes = filtered_df.groupby("classificacao")["valor_original"].sum().reset_index()
            return [
                {
                    "nome": row["classificacao"],
                    "valor": round(row["valor_original"], 2)
                }
                for _, row in classificacoes.iterrows()
            ]

        # Função auxiliar segura para obter valores mesmo que não existam no dicionário
        def get(nome):
            return dre_n2_sums.get(nome, 0.0)

        # Constrói a estrutura da DRE, passo a passo
        result = []

        # Linhas base da DRE (serão somadas para calcular os totalizadores)
        faturamento = get("Faturamento")
        tributos = get("Tributos e deduções sobre a receita")
        cmv = get("CMV")
        csp = get("CSP")
        cpv = get("CPV")
        despesas_adm = get("Despesas Administrativas")
        despesas_pessoal = get("Despesas com Pessoal")
        despesas_ocupacao = get("Despesas com Ocupação")
        despesas_comerciais = get("Despesas Comerciais")
        depre = get("Depreciação")
        amort = get("Amortização")
        receitas_fin = get("Receitas Financeiras")
        despesas_fin = get("Despesas Financeiras")
        receitas_nop = get("Receitas não operacionais")
        despesas_nop = get("Despesas não operacionais")
        irpj = get("IRPJ")
        csll = get("CSLL")

        # Começa a montar a estrutura da DRE com os cálculos intermediários
        result.append({
            "tipo": "+",
            "nome": "Faturamento",
            "valor": round(faturamento, 2),
            "classificacoes": get_classificacoes("Faturamento")
        })
        receita_bruta = faturamento
        result.append({
            "tipo": "=",
            "nome": "Receita Bruta",
            "valor": round(receita_bruta, 2)
        })

        result.append({
            "tipo": "-",
            "nome": "Tributos e deduções sobre a receita",
            "valor": round(tributos, 2),
            "classificacoes": get_classificacoes("Tributos e deduções sobre a receita")
        })
        receita_liquida = receita_bruta - tributos
        result.append({
            "tipo": "=",
            "nome": "Receita Líquida",
            "valor": round(receita_liquida, 2)
        })

        result.append({
            "tipo": "-",
            "nome": "CMV",
            "valor": round(cmv, 2),
            "classificacoes": get_classificacoes("CMV")
        })
        result.append({
            "tipo": "-",
            "nome": "CSP",
            "valor": round(csp, 2),
            "classificacoes": get_classificacoes("CSP")
        })
        result.append({
            "tipo": "-",
            "nome": "CPV",
            "valor": round(cpv, 2),
            "classificacoes": get_classificacoes("CPV")
        })
        resultado_bruto = receita_liquida - cmv - csp - cpv
        result.append({
            "tipo": "=",
            "nome": "Resultado Bruto",
            "valor": round(resultado_bruto, 2)
        })

        result.append({
            "tipo": "-",
            "nome": "Despesas Administrativas",
            "valor": round(despesas_adm, 2),
            "classificacoes": get_classificacoes("Despesas Administrativas")
        })
        result.append({
            "tipo": "-",
            "nome": "Despesas com Pessoal",
            "valor": round(despesas_pessoal, 2),
            "classificacoes": get_classificacoes("Despesas com Pessoal")
        })
        result.append({
            "tipo": "-",
            "nome": "Despesas com Ocupação",
            "valor": round(despesas_ocupacao, 2),
            "classificacoes": get_classificacoes("Despesas com Ocupação")
        })
        result.append({
            "tipo": "-",
            "nome": "Despesas Comerciais",
            "valor": round(despesas_comerciais, 2),
            "classificacoes": get_classificacoes("Despesas Comerciais")
        })
        ebitda = resultado_bruto - despesas_adm - despesas_pessoal - despesas_ocupacao - despesas_comerciais
        result.append({
            "tipo": "=",
            "nome": "EBITDA",
            "valor": round(ebitda, 2)
        })

        result.append({
            "tipo": "-",
            "nome": "Depreciação",
            "valor": round(depre, 2),
            "classificacoes": get_classificacoes("Depreciação")
        })
        result.append({
            "tipo": "-",
            "nome": "Amortização",
            "valor": round(amort, 2),
            "classificacoes": get_classificacoes("Amortização")
        })
        ebit = ebitda - depre - amort
        result.append({
            "tipo": "=",
            "nome": "EBIT",
            "valor": round(ebit, 2)
        })

        result.append({
            "tipo": "+",
            "nome": "Receitas Financeiras",
            "valor": round(receitas_fin, 2),
            "classificacoes": get_classificacoes("Receitas Financeiras")
        })
        result.append({
            "tipo": "-",
            "nome": "Despesas Financeiras",
            "valor": round(despesas_fin, 2),
            "classificacoes": get_classificacoes("Despesas Financeiras")
        })
        result.append({
            "tipo": "+",
            "nome": "Receitas não operacionais",
            "valor": round(receitas_nop, 2),
            "classificacoes": get_classificacoes("Receitas não operacionais")
        })
        result.append({
            "tipo": "-",
            "nome": "Despesas não operacionais",
            "valor": round(despesas_nop, 2),
            "classificacoes": get_classificacoes("Despesas não operacionais")
        })

        resultado_financeiro = ebit + receitas_fin - despesas_fin + receitas_nop - despesas_nop
        result.append({
            "tipo": "=",
            "nome": "Resultado Financeiro",
            "valor": round(resultado_financeiro, 2)
        })

        result.append({
            "tipo": "-",
            "nome": "IRPJ",
            "valor": round(irpj, 2),
            "classificacoes": get_classificacoes("IRPJ")
        })
        result.append({
            "tipo": "-",
            "nome": "CSLL",
            "valor": round(csll, 2),
            "classificacoes": get_classificacoes("CSLL")
        })
        resultado_liquido = resultado_financeiro - irpj - csll
        result.append({
            "tipo": "=",
            "nome": "Resultado Líquido",
            "valor": round(resultado_liquido, 2)
        })

        return result

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}