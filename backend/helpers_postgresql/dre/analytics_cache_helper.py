"""
Helper para pré-agregação e cache de análises AV/AH
Sistema inteligente que pré-calcula análises e as armazena em cache
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import text
from database.connection_sqlalchemy import get_engine
from helpers_postgresql.dre.cache_helper import get_cache
from helpers_postgresql.dre.analysis_helper_postgresql import calcular_analise_horizontal_postgresql, calcular_analise_vertical_postgresql

class AnalyticsCacheHelper:
    def __init__(self):
        self.cache = None
        self.engine = None
        
    async def initialize(self):
        """Inicializa conexões com cache e banco"""
        self.cache = await get_cache()
        self.engine = get_engine()
    
    async def get_cached_analytics(self, dre_n2_name: str, periodo: str, tipo_periodo: str) -> Optional[Dict]:
        """Busca análises em cache"""
        if not self.cache:
            await self.initialize()
            
        cache_key = f"analytics:{dre_n2_name}:{tipo_periodo}:{periodo}"
        return await self.cache.get(cache_key)
    
    async def set_cached_analytics(self, dre_n2_name: str, periodo: str, tipo_periodo: str, analytics: Dict, ttl: int = 600):
        """Salva análises em cache"""
        if not self.cache:
            await self.initialize()
            
        cache_key = f"analytics:{dre_n2_name}:{tipo_periodo}:{periodo}"
        await self.cache.set(cache_key, analytics, ttl)
    
    async def pre_calculate_analytics(self, dre_n2_name: str, tipo_periodo: str = "mensal") -> Dict[str, Any]:
        """Pré-calcula análises para uma conta DRE específica"""
        if not self.engine:
            await self.initialize()
            
        try:
            with self.engine.connect() as connection:
                # Buscar dados históricos para análises
                if tipo_periodo == "mensal":
                    query = text("""
                        SELECT 
                            TO_CHAR(competencia, 'YYYY-MM') as periodo,
                            SUM(valor_original) as valor_total
                        FROM financial_data 
                        WHERE dre_n2 = :dre_n2_name
                        AND valor_original IS NOT NULL 
                        AND competencia IS NOT NULL
                        GROUP BY TO_CHAR(competencia, 'YYYY-MM')
                        ORDER BY periodo
                    """)
                elif tipo_periodo == "trimestral":
                    query = text("""
                        SELECT 
                            CONCAT(EXTRACT(YEAR FROM competencia), '-Q', EXTRACT(QUARTER FROM competencia)) as periodo,
                            SUM(valor_original) as valor_total
                        FROM financial_data 
                        WHERE dre_n2 = :dre_n2_name
                        AND valor_original IS NOT NULL 
                        AND competencia IS NOT NULL
                        GROUP BY CONCAT(EXTRACT(YEAR FROM competencia), '-Q', EXTRACT(QUARTER FROM competencia))
                        ORDER BY periodo
                    """)
                else:  # anual
                    query = text("""
                        SELECT 
                            EXTRACT(YEAR FROM competencia)::text as periodo,
                            SUM(valor_original) as valor_total
                        FROM financial_data 
                        WHERE dre_n2 = :dre_n2_name
                        AND valor_original IS NOT NULL 
                        AND competencia IS NOT NULL
                        GROUP BY EXTRACT(YEAR FROM competencia)
                        ORDER BY periodo
                    """)
                
                result = connection.execute(query, {"dre_n2_name": dre_n2_name})
                rows = result.fetchall()
                
                if not rows:
                    return {}
                
                # Calcular análises horizontais
                analises_horizontais = {}
                for i, row in enumerate(rows):
                    if i == 0:
                        analises_horizontais[row.periodo] = "–"
                    else:
                        valor_atual = float(row.valor_total)
                        valor_anterior = float(rows[i-1].valor_total)
                        analises_horizontais[row.periodo] = calcular_analise_horizontal_postgresql(valor_atual, valor_anterior)
                
                # Calcular análises verticais (baseado no faturamento)
                analises_verticais = {}
                faturamento_query = text("""
                    SELECT 
                        TO_CHAR(competencia, 'YYYY-MM') as periodo,
                        SUM(valor_original) as valor_faturamento
                    FROM financial_data 
                    WHERE dre_n2 = '( + ) Faturamento'
                    AND valor_original IS NOT NULL 
                    AND competencia IS NOT NULL
                    GROUP BY TO_CHAR(competencia, 'YYYY-MM')
                """)
                
                faturamento_result = connection.execute(faturamento_query)
                faturamento_data = {row.periodo: float(row.valor_faturamento) for row in faturamento_result}
                
                for row in rows:
                    base = faturamento_data.get(row.periodo, 0)
                    valor = float(row.valor_total)
                    analises_verticais[row.periodo] = calcular_analise_vertical_postgresql(valor, base)
                
                # Organizar resultado
                analytics = {
                    "dre_n2": dre_n2_name,
                    "tipo_periodo": tipo_periodo,
                    "analises_horizontais": analises_horizontais,
                    "analises_verticais": analises_verticais,
                    "periodos": [row.periodo for row in rows],
                    "valores": {row.periodo: float(row.valor_total) for row in rows},
                    "ultima_atualizacao": datetime.now().isoformat()
                }
                
                return analytics
                
        except Exception as e:
            print(f"❌ Erro ao pré-calcular análises para {dre_n2_name}: {e}")
            return {}
    
    async def get_or_calculate_analytics(self, dre_n2_name: str, periodo: str, tipo_periodo: str = "mensal") -> Dict[str, Any]:
        """Busca análises em cache ou calcula se necessário"""
        # Tentar buscar do cache primeiro
        cached_analytics = await self.get_cached_analytics(dre_n2_name, periodo, tipo_periodo)
        
        if cached_analytics:
            return cached_analytics
        
        # Se não estiver em cache, pré-calcular
        print(f"🔄 Pré-calculando análises para {dre_n2_name} ({tipo_periodo})")
        analytics = await self.pre_calculate_analytics(dre_n2_name, tipo_periodo)
        
        if analytics:
            # Salvar em cache para uso futuro
            await self.set_cached_analytics(dre_n2_name, periodo, tipo_periodo, analytics)
            print(f"✅ Análises pré-calculadas e cacheadas para {dre_n2_name}")
        
        return analytics
    
    async def batch_pre_calculate_analytics(self, dre_n2_names: List[str], tipo_periodo: str = "mensal"):
        """Pré-calcula análises para múltiplas contas em lote"""
        print(f"🚀 Iniciando pré-cálculo em lote para {len(dre_n2_names)} contas...")
        
        tasks = []
        for dre_n2_name in dre_n2_names:
            task = self.pre_calculate_analytics(dre_n2_name, tipo_periodo)
            tasks.append(task)
        
        # Executar em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Erro ao pré-calcular {dre_n2_names[i]}: {result}")
            else:
                success_count += 1
        
        print(f"✅ Pré-cálculo em lote concluído: {success_count}/{len(dre_n2_names)} contas processadas")
        return success_count
    
    async def invalidate_analytics_cache(self, dre_n2_name: str = None):
        """Invalida cache de análises"""
        if not self.cache:
            await self.initialize()
            
        if dre_n2_name:
            # Invalidar cache específico
            pattern = f"analytics:{dre_n2_name}:*"
        else:
            # Invalidar todo o cache de análises
            pattern = "analytics:*"
            
        await self.cache.delete_pattern(pattern)
        print(f"🗑️ Cache de análises invalidado para: {dre_n2_name or 'todas as contas'}")

# Instância global
analytics_cache = AnalyticsCacheHelper()

async def get_analytics_cache() -> AnalyticsCacheHelper:
    """Retorna instância do helper de cache de análises"""
    if not analytics_cache.cache:
        await analytics_cache.initialize()
    return analytics_cache
