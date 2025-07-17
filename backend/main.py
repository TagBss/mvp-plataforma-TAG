import os
import time
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from endpoints.dre import router as dre_router
from endpoints.dfc import router as dfc_router


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
        "https://mvp-plataforma-tag.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers dos endpoints
app.include_router(dre_router, tags=["DRE"])
app.include_router(dfc_router, tags=["DFC"])

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

def calcular_mom_faturamento(df_filtrado, date_column):
    """
    Calcula variação Month over Month (MoM) para faturamento usando valor_original
    """
    try:
        # Agrupar por mês e somar valores
        df_mensal = df_filtrado.groupby(
            df_filtrado[date_column].dt.to_period('M')
        )['valor_original'].sum().reset_index()
        
        # Ordenar por data
        df_mensal = df_mensal.sort_values(date_column)
        
        # Calcular variação MoM
        df_mensal['valor_anterior'] = df_mensal['valor_original'].shift(1)
        df_mensal['variacao_absoluta'] = df_mensal['valor_original'] - df_mensal['valor_anterior']
        df_mensal['variacao_percentual'] = (
            (df_mensal['valor_original'] - df_mensal['valor_anterior']) / 
            df_mensal['valor_anterior'] * 100
        ).round(2)
        
        # Preparar dados para retorno
        mom_data = []
        for _, row in df_mensal.iterrows():
            mom_data.append({
                "mes": str(row[date_column]),
                "valor_atual": round(row['valor_original'], 2),
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
                df_pmr["data_caixa"] = data_caixa_col[mask]
                df_pmr["competencia"] = pd.to_datetime(df_pmr["competencia"])
                df_pmr["diferenca_dias"] = (df_pmr["data_caixa"] - df_pmr["competencia"]).dt.days
                pmr = df_pmr["diferenca_dias"].mean()

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
                df_pmp["data_caixa"] = data_caixa_col[mask]
                df_pmp["competencia"] = pd.to_datetime(df_pmp["competencia"])
                df_pmp["diferenca_dias"] = (df_pmp["data_caixa"] - df_pmp["competencia"]).dt.days
                pmp = df_pmp["diferenca_dias"].mean()

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

@app.get("/faturamento")
def get_faturamento(mes: str = None):
    return calcular_faturamento(mes)

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
            return {"error": "Erro ao calcular movimentações"}

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
            cap_item = mom_cap.get(mes, {})
            car_item = mom_car.get(mes, {})
            valor_atual = (cap_item.get("valor_atual", 0) or 0) + (car_item.get("valor_atual", 0) or 0)
            valor_anterior = None
            if cap_item.get("valor_anterior") is not None and car_item.get("valor_anterior") is not None:
                valor_anterior = cap_item["valor_anterior"] + car_item["valor_anterior"]
            
            variacao_absoluta = None
            variacao_percentual = None
            if valor_anterior is not None:
                variacao_absoluta = valor_atual - valor_anterior
                variacao_percentual = (variacao_absoluta / valor_anterior * 100) if valor_anterior != 0 else None
            
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
            return {"error": "Erro ao calcular evolução de saldos"}

        mom_cap = {item["mes"]: item for item in cap["data"].get("mom_analysis", [])}
        mom_car = {item["mes"]: item for item in car["data"].get("mom_analysis", [])}
        all_meses = sorted(set(mom_cap.keys()) | set(mom_car.keys()))

        evolucao = []
        saldo_inicial = 0.0
        for idx, mes in enumerate(all_meses):
            cap_item = mom_cap.get(mes, {})
            car_item = mom_car.get(mes, {})
            movimentacao = (cap_item.get("valor_atual", 0) or 0) + (car_item.get("valor_atual", 0) or 0)
            saldo_final = saldo_inicial + movimentacao
            
            evolucao.append({
                "mes": mes,
                "saldo_inicial": round(saldo_inicial, 2),
                "movimentacao": round(movimentacao, 2),
                "saldo_final": round(saldo_final, 2)
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
            variacao_percentual = (variacao_absoluta / valor_anterior * 100) if valor_anterior != 0 else None
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

def calcular_faturamento(mes_filtro: str = None):
    """
    Calcula faturamento baseado em:
    - Coluna: valor_original
    - Filtros: origem = "FAT" e DRE_n2 = "Faturamento"
    """
    filename = "financial-data-roriz.xlsx"
    
    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Validação das colunas obrigatórias
        required_columns = ["valor_original", "origem", "DRE_n2", "competencia"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        # Identificar coluna de data (usar competencia para faturamento)
        date_column = "competencia"

        # Processar dados
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df["valor_original"] = pd.to_numeric(df["valor_original"], errors="coerce")

        df = df.dropna(subset=[date_column, "valor_original"])

        # Filtrar por origem = "FAT" e DRE_n2 = "Faturamento"
        df_fat = df[
            (df["origem"] == "FAT") & 
            (df["DRE_n2"] == "Faturamento")
        ].copy()

        # Filtrar para MoM (NÃO filtra por mês - sempre todos os meses)
        df_mom = df_fat.copy()

        # Calcular MoM SEM filtro de mês - usar função adaptada para valor_original
        mom_data = calcular_mom_faturamento(df_mom, date_column)

        # Filtrar por mês se especificado
        df_filtrado = df_fat.copy()
        if mes_filtro:
            df_filtrado = df_filtrado[
                df_filtrado[date_column].dt.strftime("%Y-%m") == mes_filtro
            ]

        if df_filtrado.empty:
            return {
                "error": f"Não foram encontrados registros de faturamento",
                "total_faturamento": 0,
                "anos_disponiveis": [],
                "meses_disponiveis": []
            }

        # Soma total do faturamento
        total_faturamento = df_filtrado["valor_original"].sum()
        total_registros = len(df_filtrado)

        # Anos e meses disponíveis
        if not mes_filtro:
            # Se for todo o período, pegue todos os meses/anos disponíveis
            anos_disponiveis = sorted(df_fat[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_fat[date_column].dt.strftime("%Y-%m").unique().tolist())
        else:
            anos_disponiveis = sorted(df_filtrado[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_filtrado[date_column].dt.strftime("%Y-%m").unique().tolist())

        return {
            "success": True,
            "data": {
                "total_faturamento": round(total_faturamento, 2),
                "data_calculo": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "estatisticas": {
                    "total_registros": total_registros
                },
                "anos_disponiveis": anos_disponiveis,
                "meses_disponiveis": meses_disponiveis,
                "mom_analysis": mom_data
            }
        }
        
    except Exception as e:
        return {"error": f"Erro ao calcular faturamento: {str(e)}"}

@app.get("/faturamento")
def get_faturamento(mes: str = None):
    return calcular_faturamento(mes)

