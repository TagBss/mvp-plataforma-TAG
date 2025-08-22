import os
import time
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from endpoints.dre import router as dre_router
from endpoints.dfc import router as dfc_router
from endpoints.financial_data_sqlalchemy import router as financial_data_router
from endpoints.financial_data_specialized import router as financial_data_specialized_router
from endpoints.database_admin import router as database_admin_router
from endpoints.dre_postgresql import router as dre_postgresql_router
from endpoints.dre_postgresql_simple import router as dre_postgresql_simple_router
from endpoints.dre_postgresql_debug import router as dre_postgresql_debug_router
from endpoints.dre_postgresql_views import router as dre_postgresql_views_router
from endpoints.dre_n0_postgresql import router as dre_n0_postgresql_router
from endpoints.backup_admin import router as backup_admin_router
from auth import auth_router


# --- CACHE GLOBAL PARA O DATAFRAME ---
_df_cache = {
    "df": None,
    "last_loaded": 0,
    "last_mtime": 0,
}
CACHE_TIMEOUT = 300  # 5 minutos ao invés de 1 minuto

def get_cached_df(filename="db_bluefit - Copia.xlsx"):
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
            print(f"📂 Carregando arquivo Excel: {filename}")
            start_time = time.time()
            
            # Otimizar leitura do Excel
            df = pd.read_excel(
                filename,
                engine='openpyxl',  # Engine mais rápida
                na_values=['', 'NaN', 'N/A', 'null'],  # Valores nulos explícitos
            )
            
            end_time = time.time()
            print(f"⏱️ Arquivo carregado em {end_time - start_time:.2f}s")
            print(f"📊 Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
            
            _df_cache["df"] = df
            _df_cache["last_loaded"] = now
            _df_cache["last_mtime"] = mtime
        except Exception as e:
            print(f"❌ Erro ao carregar Excel: {e}")
            _df_cache["df"] = None
    return _df_cache["df"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers dos endpoints
app.include_router(auth_router, tags=["authentication"])
app.include_router(dre_router, tags=["DRE"])
app.include_router(dfc_router, tags=["DFC"])
app.include_router(financial_data_router, tags=["financial-data"])
app.include_router(financial_data_specialized_router, tags=["financial-data-specialized"])
app.include_router(database_admin_router, tags=["database-admin"])
app.include_router(dre_postgresql_router, tags=["dre-postgresql"])
app.include_router(dre_postgresql_simple_router, tags=["dre-postgresql-simple"])
app.include_router(dre_postgresql_debug_router, tags=["dre-postgresql-debug"])
app.include_router(dre_postgresql_views_router, tags=["dre-postgresql-views"])
app.include_router(dre_n0_postgresql_router, tags=["dre-n0-postgresql"])
app.include_router(backup_admin_router, tags=["admin-backups"])

@app.get("/")
def root():
    return {"message": "API está funcionando!"}

@app.get("/health")
def health_check():
    """Endpoint para verificar saúde do sistema e performance"""
    start_time = time.time()
    
    try:
        # Verificar se o arquivo existe
        filename = "db_bluefit - Copia.xlsx"
        if not os.path.exists(filename):
            return {
                "status": "error",
                "message": "Arquivo de dados não encontrado",
                "response_time": time.time() - start_time
            }
        
        # Verificar cache
        cache_status = "hit" if _df_cache["df"] is not None else "miss"
        
        # Verificar se consegue carregar dados
        df = get_cached_df(filename)
        if df is None:
            return {
                "status": "error", 
                "message": "Erro ao carregar dados",
                "cache_status": cache_status,
                "response_time": time.time() - start_time
            }
        
        return {
            "status": "healthy",
            "message": "Sistema operacional",
            "data_rows": len(df),
            "data_columns": len(df.columns),
            "cache_status": cache_status,
            "cache_age": time.time() - _df_cache["last_loaded"] if _df_cache["last_loaded"] > 0 else None,
            "response_time": time.time() - start_time
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "response_time": time.time() - start_time
        }