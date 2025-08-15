"""
Configurações para Redis e Cache
"""
import os
from typing import Optional

# Configurações do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_TTL = int(os.getenv("REDIS_TTL", "300"))  # 5 minutos padrão

# Configurações de Cache
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
ENABLE_MATERIALIZED_VIEWS = os.getenv("ENABLE_MATERIALIZED_VIEWS", "true").lower() == "true"
ENABLE_PERFORMANCE_INDEXES = os.getenv("ENABLE_PERFORMANCE_INDEXES", "true").lower() == "true"

# Configurações de Performance
ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
CACHE_STATS_ENABLED = os.getenv("CACHE_STATS_ENABLED", "true").lower() == "true"

# Configurações de TTL específicas
DRE_N0_CACHE_TTL = int(os.getenv("DRE_N0_CACHE_TTL", "300"))  # 5 minutos
CLASSIFICACOES_CACHE_TTL = int(os.getenv("CLASSIFICACOES_CACHE_TTL", "300"))  # 5 minutos
ANALYTICS_CACHE_TTL = int(os.getenv("ANALYTICS_CACHE_TTL", "600"))  # 10 minutos

# Configurações de invalidação
CACHE_INVALIDATION_ENABLED = os.getenv("CACHE_INVALIDATION_ENABLED", "true").lower() == "true"
AUTO_REFRESH_MATERIALIZED_VIEWS = os.getenv("AUTO_REFRESH_MATERIALIZED_VIEWS", "false").lower() == "true"

def get_redis_config() -> dict:
    """Retorna configurações do Redis"""
    return {
        "url": REDIS_URL,
        "ttl": REDIS_TTL,
        "enable_cache": ENABLE_CACHE,
        "enable_materialized_views": ENABLE_MATERIALIZED_VIEWS,
        "enable_performance_indexes": ENABLE_PERFORMANCE_INDEXES,
        "enable_performance_logging": ENABLE_PERFORMANCE_LOGGING,
        "cache_stats_enabled": CACHE_STATS_ENABLED,
        "dre_n0_cache_ttl": DRE_N0_CACHE_TTL,
        "classificacoes_cache_ttl": CLASSIFICACOES_CACHE_TTL,
        "analytics_cache_ttl": ANALYTICS_CACHE_TTL,
        "cache_invalidation_enabled": CACHE_INVALIDATION_ENABLED,
        "auto_refresh_materialized_views": AUTO_REFRESH_MATERIALIZED_VIEWS
    }

def print_config():
    """Imprime configurações atuais"""
    config = get_redis_config()
    print("🔧 Configurações Redis e Cache:")
    print("=" * 40)
    for key, value in config.items():
        print(f"  {key}: {value}")
    print("=" * 40)
