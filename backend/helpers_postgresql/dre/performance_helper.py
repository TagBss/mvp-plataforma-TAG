"""
Helper para otimizações de performance da Fase 3
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.engine import Connection
from helpers_postgresql.dre.cache_helper import get_cache

class PerformanceHelper:
    """Helper para otimizações de performance da Fase 3"""
    
    @staticmethod
    async def debounce_request(cache_key: str, ttl: int = 60) -> bool:
        """Implementa debounce para evitar requisições excessivas"""
        try:
            cache = await get_cache()
            last_request = await cache.get(f"debounce:{cache_key}")
            
            if last_request:
                # Verificar se passou tempo suficiente desde a última requisição
                last_time = datetime.fromisoformat(last_request)
                if datetime.now() - last_time < timedelta(seconds=ttl):
                    return False  # Muito cedo para nova requisição
            
            # Registrar nova requisição
            await cache.set(f"debounce:{cache_key}", datetime.now().isoformat(), ttl=ttl)
            return True
            
        except Exception as e:
            print(f"❌ Erro no debounce: {e}")
            return True  # Em caso de erro, permitir a requisição
    
    @staticmethod
    async def compress_historical_data(data: Dict[str, Any], compression_ratio: float = 0.8) -> Dict[str, Any]:
        """Comprime dados históricos para reduzir tamanho de transferência"""
        try:
            compressed_data = data.copy()
            
            # Comprimir valores numéricos (arredondar para reduzir precisão)
            if 'data' in compressed_data:
                for item in compressed_data['data']:
                    if 'valores_mensais' in item:
                        item['valores_mensais'] = {
                            k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in item['valores_mensais'].items()
                        }
                    
                    if 'valores_trimestrais' in item:
                        item['valores_trimestrais'] = {
                            k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in item['valores_trimestrais'].items()
                        }
                    
                    if 'valores_anuais' in item:
                        item['valores_anuais'] = {
                            k: round(v, 2) if isinstance(v, (int, float)) else v
                            for k, v in item['valores_anuais'].items()
                        }
            
            # Adicionar metadados de compressão
            compressed_data['_compression'] = {
                'compressed_at': datetime.now().isoformat(),
                'compression_ratio': compression_ratio,
                'original_size': len(str(data)),
                'compressed_size': len(str(compressed_data))
            }
            
            return compressed_data
            
        except Exception as e:
            print(f"❌ Erro na compressão: {e}")
            return data
    
    @staticmethod
    async def monitor_performance(operation_name: str, start_time: float) -> Dict[str, Any]:
        """Monitora performance de operações"""
        try:
            execution_time = time.time() - start_time
            
            # Categorizar performance
            if execution_time < 0.1:
                performance_level = "excellent"
            elif execution_time < 0.5:
                performance_level = "good"
            elif execution_time < 1.0:
                performance_level = "acceptable"
            else:
                performance_level = "slow"
            
            # Salvar métricas no cache para análise
            cache = await get_cache()
            metrics_key = f"performance:{operation_name}:{datetime.now().strftime('%Y-%m-%d')}"
            
            current_metrics = await cache.get(metrics_key) or {
                'operation': operation_name,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_requests': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'performance_levels': {'excellent': 0, 'good': 0, 'acceptable': 0, 'slow': 0}
            }
            
            # Atualizar métricas
            current_metrics['total_requests'] += 1
            current_metrics['total_time'] += execution_time
            current_metrics['min_time'] = min(current_metrics['min_time'], execution_time)
            current_metrics['max_time'] = max(current_metrics['max_time'], execution_time)
            current_metrics['performance_levels'][performance_level] += 1
            
            # Salvar no cache
            await cache.set(metrics_key, current_metrics, ttl=86400)  # 24 horas
            
            return {
                "operation": operation_name,
                "execution_time": execution_time,
                "performance_level": performance_level,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            return {
                "operation": operation_name,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    @staticmethod
    async def get_performance_metrics(operation_name: str = None, date: str = None) -> Dict[str, Any]:
        """Obtém métricas de performance"""
        try:
            cache = await get_cache()
            
            if operation_name and date:
                # Métricas específicas
                metrics_key = f"performance:{operation_name}:{date}"
                metrics = await cache.get(metrics_key)
                
                if metrics:
                    avg_time = metrics['total_time'] / metrics['total_requests'] if metrics['total_requests'] > 0 else 0
                    metrics['average_time'] = avg_time
                    return metrics
                else:
                    return {"error": "Métricas não encontradas"}
            
            else:
                # Todas as métricas disponíveis
                pattern = "performance:*"
                keys = await cache.redis.keys(pattern) if cache.redis else []
                
                all_metrics = {}
                for key in keys:
                    metrics = await cache.get(key)
                    if metrics:
                        operation = metrics.get('operation', 'unknown')
                        all_metrics[operation] = metrics
                
                return all_metrics
                
        except Exception as e:
            print(f"❌ Erro ao obter métricas: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def optimize_query_performance(connection: Connection, query_name: str) -> Dict[str, Any]:
        """Otimiza performance de queries específicas"""
        try:
            # Verificar estatísticas das tabelas
            analyze_query = text("ANALYZE")
            connection.execute(analyze_query)
            
            # Verificar índices existentes
            indexes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename IN ('financial_data', 'dre_structure_n0')
                ORDER BY tablename, indexname
            """)
            
            indexes_result = connection.execute(indexes_query)
            indexes = [{"table": row.tablename, "index": row.indexname, "definition": row.indexdef} for row in indexes_result]
            
            # Verificar estatísticas de tabelas
            stats_query = text("""
                SELECT 
                    schemaname,
                    relname as tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE relname IN ('financial_data', 'dre_structure_n0')
                ORDER BY relname
            """)
            
            stats_result = connection.execute(stats_query)
            stats = [{
                "table": row.tablename,
                "inserts": row.n_tup_ins,
                "updates": row.n_tup_upd,
                "deletes": row.n_tup_del,
                "live_tuples": row.n_live_tup,
                "dead_tuples": row.n_dead_tup,
                "last_vacuum": row.last_vacuum,
                "last_autovacuum": row.last_autovacuum,
                "last_analyze": row.last_analyze,
                "last_autoanalyze": row.last_autoanalyze
            } for row in stats_result]
            
            return {
                "success": True,
                "query_name": query_name,
                "indexes": indexes,
                "statistics": stats,
                "optimization_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
