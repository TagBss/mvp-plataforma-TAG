import pandas as pd
import time
import os

# --- CACHE GLOBAL PARA O DATAFRAME ---
_df_cache = {
    "df": None,
    "last_loaded": 0,
    "last_mtime": 0,
}
CACHE_TIMEOUT = 300  # 5 minutos

def get_cached_df(filename="db_bluefit - Copia.xlsx"):
    """Carrega e gerencia cache do dataframe principal"""
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
            start_time = time.time()
            
            # Otimizar leitura do Excel - especificar aba "base"
            df = pd.read_excel(
                filename,
                sheet_name="base",  # Especificar aba "base"
                engine='openpyxl',  # Engine mais rápida
                na_values=['', 'NaN', 'N/A', 'null'],  # Valores nulos explícitos
            )
            
            end_time = time.time()
            
            _df_cache["df"] = df
            _df_cache["last_loaded"] = now
            _df_cache["last_mtime"] = mtime
        except Exception as e:
            _df_cache["df"] = None
    return _df_cache["df"]

def clear_cache():
    """Limpa o cache global"""
    global _df_cache
    _df_cache = {
        "df": None,
        "last_loaded": 0,
        "last_mtime": 0,
    } 