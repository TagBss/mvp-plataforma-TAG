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

        # Verifica se existe coluna de data/mês
        date_column = None
        possible_date_columns = ['data', 'mes', 'month', 'date', 'periodo', 'competencia', 'emissao']
        for col in possible_date_columns:
            if col in df.columns:
                date_column = col
                break

        # Se não encontrou coluna de data, converte a primeira coluna que pareça ser data
        if date_column is None:
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]' or 'data' in col.lower() or 'mes' in col.lower():
                    date_column = col
                    break

        # Converte a coluna de data para datetime se necessário
        if date_column:
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            # Cria coluna de mês/ano
            df['mes_ano'] = df[date_column].dt.to_period('M').astype(str)
            # Obtém lista de meses únicos ordenados
            meses_unicos = sorted(df['mes_ano'].dropna().unique())
        else:
            meses_unicos = []

        # Agrupa os valores por DRE_n2 (total geral)
        dre_n2_sums = df.groupby("DRE_n2")["valor_original"].sum().to_dict()

        # Agrupa os valores por DRE_n2 e mês (se houver coluna de data)
        monthly_data = {}
        if date_column and meses_unicos:
            for mes in meses_unicos:
                df_mes = df[df['mes_ano'] == mes]
                monthly_data[mes] = df_mes.groupby("DRE_n2")["valor_original"].sum().to_dict()

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

        # Função auxiliar segura para obter valores (total geral)
        def get(nome):
            return dre_n2_sums.get(nome, 0.0)

        # Função auxiliar para obter valores mensais
        def get_monthly(nome, mes):
            return monthly_data.get(mes, {}).get(nome, 0.0)

        # Constrói a estrutura da DRE
        result = []

        # Linhas base da DRE
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

        # Valores totais
        valores_totais = {nome: get(nome) for nome, _ in contas_dre}

        # Valores mensais
        valores_mensais = {}
        for mes in meses_unicos:
            valores_mensais[mes] = {nome: get_monthly(nome, mes) for nome, _ in contas_dre}

        # Função para calcular linha de resultado
        def calcular_linha_resultado(nome, formula_func, tipo="="):
            item = {
                "tipo": tipo,
                "nome": nome,
                "valor": round(formula_func(valores_totais), 2)
            }
            
            # Adiciona valores mensais
            if meses_unicos:
                item["valores_mensais"] = {}
                for mes in meses_unicos:
                    item["valores_mensais"][mes] = round(formula_func(valores_mensais[mes]), 2)
            
            return item

        # Função para criar linha de conta
        def criar_linha_conta(nome, tipo):
            item = {
                "tipo": tipo,
                "nome": nome,
                "valor": round(valores_totais[nome], 2),
                "classificacoes": get_classificacoes(nome)
            }
            
            # Adiciona valores mensais
            if meses_unicos:
                item["valores_mensais"] = {}
                for mes in meses_unicos:
                    item["valores_mensais"][mes] = round(valores_mensais[mes][nome], 2)
            
            return item

        # Monta a DRE
        result.append(criar_linha_conta("Faturamento", "+"))
        result.append(calcular_linha_resultado("Receita Bruta", lambda v: v["Faturamento"]))

        result.append(criar_linha_conta("Tributos e deduções sobre a receita", "-"))
        result.append(calcular_linha_resultado("Receita Líquida", 
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"]))

        result.append(criar_linha_conta("CMV", "-"))
        result.append(criar_linha_conta("CSP", "-"))
        result.append(criar_linha_conta("CPV", "-"))
        result.append(calcular_linha_resultado("Resultado Bruto",
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"]))

        result.append(criar_linha_conta("Despesas Administrativas", "-"))
        result.append(criar_linha_conta("Despesas com Pessoal", "-"))
        result.append(criar_linha_conta("Despesas com Ocupação", "-"))
        result.append(criar_linha_conta("Despesas Comerciais", "-"))
        result.append(calcular_linha_resultado("EBITDA",
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] - 
                     v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"]))

        result.append(criar_linha_conta("Depreciação", "-"))
        result.append(criar_linha_conta("Amortização", "-"))
        result.append(calcular_linha_resultado("EBIT",
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] - 
                     v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
                     v["Depreciação"] - v["Amortização"]))

        result.append(criar_linha_conta("Receitas Financeiras", "+"))
        result.append(criar_linha_conta("Despesas Financeiras", "-"))
        result.append(criar_linha_conta("Receitas não operacionais", "+"))
        result.append(criar_linha_conta("Despesas não operacionais", "-"))
        result.append(calcular_linha_resultado("Resultado Financeiro",
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] - 
                     v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
                     v["Depreciação"] - v["Amortização"] + v["Receitas Financeiras"] - v["Despesas Financeiras"] +
                     v["Receitas não operacionais"] - v["Despesas não operacionais"]))

        result.append(criar_linha_conta("IRPJ", "-"))
        result.append(criar_linha_conta("CSLL", "-"))
        result.append(calcular_linha_resultado("Resultado Líquido",
            lambda v: v["Faturamento"] - v["Tributos e deduções sobre a receita"] - v["CMV"] - v["CSP"] - v["CPV"] - 
                     v["Despesas Administrativas"] - v["Despesas com Pessoal"] - v["Despesas com Ocupação"] - v["Despesas Comerciais"] -
                     v["Depreciação"] - v["Amortização"] + v["Receitas Financeiras"] - v["Despesas Financeiras"] +
                     v["Receitas não operacionais"] - v["Despesas não operacionais"] - v["IRPJ"] - v["CSLL"]))

        # Adiciona informações sobre os meses na resposta
        response = {
            "meses": meses_unicos,
            "data": result
        }

        return response

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}