"""
Helpers PostgreSQL - versão independente da versão Excel
"""

from .dre_n0_helper import DreN0Helper
from .classificacoes_helper import ClassificacoesHelper
from .pagination_helper import PaginationHelper
from .debug_helper import DebugHelper
from .performance_helper import PerformanceHelper
from .cache_helper import RedisCache, get_cache
from .analytics_cache_helper import AnalyticsCacheHelper, get_analytics_cache
from .analysis_helper_postgresql import (
    calcular_analise_horizontal_postgresql,
    calcular_analise_vertical_postgresql,
    calcular_realizado_vs_orcado_postgresql,
    calcular_analises_completas_postgresql,
    calcular_analises_horizontais_movimentacoes_postgresql
)
from .data_processor_postgresql import (
    processar_dados_financeiros_postgresql,
    separar_realizado_orcamento_postgresql,
    calcular_totais_por_periodo_postgresql,
    calcular_totalizadores_postgresql,
    calcular_mom_postgresql,
    calcular_pmr_pmp_postgresql
)

__all__ = [
    # Helpers principais
    'DreN0Helper',
    'ClassificacoesHelper',
    'PaginationHelper',
    'DebugHelper',
    'PerformanceHelper',
    
    # Cache
    'RedisCache',
    'get_cache',
    'AnalyticsCacheHelper',
    'get_analytics_cache',
    
    # Análises
    'calcular_analise_horizontal_postgresql',
    'calcular_analise_vertical_postgresql',
    'calcular_realizado_vs_orcado_postgresql',
    'calcular_analises_completas_postgresql',
    'calcular_analises_horizontais_movimentacoes_postgresql',
    
    # Processamento de dados
    'processar_dados_financeiros_postgresql',
    'separar_realizado_orcamento_postgresql',
    'calcular_totais_por_periodo_postgresql',
    'calcular_totalizadores_postgresql',
    'calcular_mom_postgresql',
    'calcular_pmr_pmp_postgresql'
]
