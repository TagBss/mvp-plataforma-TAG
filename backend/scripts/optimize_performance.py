#!/usr/bin/env python3
"""
Script para otimizar performance do DRE N0
Executa todas as otimizações de Fase 1: Cache Redis, Índices e View Materializada
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection_sqlalchemy import DATABASE_URL
from helpers_postgresql.dre.cache_helper import get_cache

async def create_performance_indexes():
    """Cria índices compostos otimizados"""
    print("🔧 Criando índices de performance...")
    
    try:
        import psycopg2
        
        # Conectar diretamente com psycopg2 para CREATE INDEX CONCURRENTLY
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # 1. Índice composto para queries principais do DRE
            print("  📊 Criando idx_financial_data_dre_comp...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_dre_comp 
                ON financial_data (dre_n2, dre_n1, competencia, valor_original)
            """)
            
            # 2. Índice composto para filtros por período
            print("  📅 Criando idx_financial_data_periodo...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_periodo 
                ON financial_data (competencia, dre_n2, valor_original)
            """)
            
            # 3. Índice composto para classificações
            print("  🏷️ Criando idx_financial_data_classificacoes...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_classificacoes 
                ON financial_data (dre_n2, classificacao, competencia, valor_original)
            """)
            
            # 4. Índice para estrutura DRE N0
            print("  🏗️ Criando idx_dre_structure_n0_active_order...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dre_structure_n0_active_order 
                ON dre_structure_n0 (is_active, order_index)
            """)
            
            # 5. Índice para competência
            print("  ⏰ Criando idx_financial_data_competencia...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_competencia 
                ON financial_data (competencia)
            """)
            
            # 6. Índice composto para análises
            print("  📈 Criando idx_financial_data_analises...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_analises 
                ON financial_data (dre_n2, competencia, valor_original)
            """)
            
            # 7. Índice para valores não nulos
            print("  💰 Criando idx_financial_data_valor_not_null...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_valor_not_null 
                ON financial_data (valor_original) WHERE valor_original IS NOT NULL
            """)
            
            # 8. Índice para dre_n2 não nulos
            print("  🏢 Criando idx_financial_data_dre2_not_null...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_dre2_not_null 
                ON financial_data (dre_n2) WHERE dre_n2 IS NOT NULL
            """)
            
            # Atualizar estatísticas
            print("  📊 Atualizando estatísticas...")
            cursor.execute("ANALYZE financial_data")
            cursor.execute("ANALYZE dre_structure_n0")
            
            print("✅ Índices de performance criados com sucesso!")
            
        conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao criar índices: {e}")
        return False
    
    return True

async def create_materialized_view():
    """Cria view materializada para análises pré-calculadas"""
    print("🔧 Criando view materializada para análises...")
    
    try:
        import psycopg2
        
        # Conectar diretamente com psycopg2 para CREATE INDEX CONCURRENTLY
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Criar view materializada
            print("  📊 Criando mv_dre_n0_analytics...")
            cursor.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dre_n0_analytics AS
                WITH dados_agregados AS (
                    SELECT 
                        fd.dre_n2,
                        fd.dre_n1,
                        fd.competencia,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                        SUM(fd.valor_original) as valor_total
                    FROM financial_data fd
                    WHERE fd.dre_n2 IS NOT NULL 
                    AND fd.valor_original IS NOT NULL 
                    AND fd.competencia IS NOT NULL
                    GROUP BY fd.dre_n2, fd.dre_n1, fd.competencia
                ),
                analises_horizontais AS (
                    SELECT 
                        dre_n2,
                        dre_n1,
                        periodo_mensal,
                        periodo_trimestral,
                        periodo_anual,
                        valor_total,
                        LAG(valor_total) OVER (
                            PARTITION BY dre_n2, dre_n1 
                            ORDER BY competencia
                        ) as valor_anterior_mensal,
                        LAG(valor_total) OVER (
                            PARTITION BY dre_n2, dre_n1 
                            ORDER BY periodo_trimestral
                        ) as valor_anterior_trimestral,
                        LAG(valor_total) OVER (
                            PARTITION BY dre_n2, dre_n1 
                            ORDER BY periodo_anual
                        ) as valor_anterior_anual
                    FROM dados_agregados
                ),
                analises_verticais AS (
                    SELECT 
                        dre_n2,
                        dre_n1,
                        periodo_mensal,
                        periodo_trimestral,
                        periodo_anual,
                        valor_total,
                        SUM(valor_total) OVER (PARTITION BY periodo_mensal) as total_mensal,
                        SUM(valor_total) OVER (PARTITION BY periodo_trimestral) as total_trimestral,
                        SUM(valor_total) OVER (PARTITION BY periodo_anual) as total_anual
                    FROM dados_agregados
                )
                SELECT 
                    ah.dre_n2,
                    ah.dre_n1,
                    ah.periodo_mensal,
                    ah.periodo_trimestral,
                    ah.periodo_anual,
                    ah.valor_total,
                    CASE 
                        WHEN ah.valor_anterior_mensal IS NULL OR ah.valor_anterior_mensal = 0 THEN '–'
                        ELSE ROUND(((ah.valor_total - ah.valor_anterior_mensal) / ah.valor_anterior_mensal * 100), 2)::text || '%'
                    END as analise_horizontal_mensal,
                    CASE 
                        WHEN ah.valor_anterior_trimestral IS NULL OR ah.valor_anterior_trimestral = 0 THEN '–'
                        ELSE ROUND(((ah.valor_total - ah.valor_anterior_trimestral) / ah.valor_anterior_trimestral * 100), 2)::text || '%'
                    END as analise_horizontal_trimestral,
                    CASE 
                        WHEN ah.valor_anterior_anual IS NULL OR ah.valor_anterior_anual = 0 THEN '–'
                        ELSE ROUND(((ah.valor_total - ah.valor_anterior_anual) / ah.valor_anterior_anual * 100), 2)::text || '%'
                    END as analise_horizontal_anual,
                    CASE 
                        WHEN av.total_mensal = 0 THEN '–'
                        ELSE ROUND((ah.valor_total / av.total_mensal * 100), 2)::text || '%'
                    END as analise_vertical_mensal,
                    CASE 
                        WHEN av.total_trimestral = 0 THEN '–'
                        ELSE ROUND((ah.valor_total / av.total_trimestral * 100), 2)::text || '%'
                    END as analise_vertical_trimestral,
                    CASE 
                        WHEN av.total_anual = 0 THEN '–'
                        ELSE ROUND((ah.valor_total / av.total_anual * 100), 2)::text || '%'
                    END as analise_vertical_anual,
                    NOW() as ultima_atualizacao
                FROM analises_horizontais ah
                JOIN analises_verticais av ON (
                    ah.dre_n2 = av.dre_n2 
                    AND ah.dre_n1 = av.dre_n1 
                    AND ah.periodo_mensal = av.periodo_mensal
                    AND ah.periodo_trimestral = av.periodo_trimestral
                    AND ah.periodo_anual = av.periodo_anual
                )
            """)
            
            # Criar índices na view materializada
            print("  📊 Criando índices na view materializada...")
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_dre2 
                ON mv_dre_n0_analytics (dre_n2)
            """)
            
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_periodo 
                ON mv_dre_n0_analytics (periodo_mensal, periodo_trimestral, periodo_anual)
            """)
            
            cursor.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_completo 
                ON mv_dre_n0_analytics (dre_n2, periodo_mensal, periodo_trimestral, periodo_anual)
            """)
            
            # Atualizar estatísticas
            print("  📊 Atualizando estatísticas da view materializada...")
            cursor.execute("ANALYZE mv_dre_n0_analytics")
            
            print("✅ View materializada criada com sucesso!")
            
        conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao criar view materializada: {e}")
        return False
    
    return True

async def test_cache():
    """Testa a conexão com Redis"""
    print("🔧 Testando conexão com Redis...")
    
    try:
        cache = await get_cache()
        await cache.connect()
        
        # Testar operações básicas
        test_key = "test:performance"
        test_data = {"message": "Teste de cache", "timestamp": "2025-01-01"}
        
        # Testar SET
        success = await cache.set(test_key, test_data, ttl=60)
        if success:
            print("  ✅ SET no cache funcionando")
        else:
            print("  ❌ SET no cache falhou")
            return False
        
        # Testar GET
        retrieved_data = await cache.get(test_key)
        if retrieved_data and retrieved_data.get("message") == "Teste de cache":
            print("  ✅ GET do cache funcionando")
        else:
            print("  ❌ GET do cache falhou")
            return False
        
        # Testar DELETE
        success = await cache.delete(test_key)
        if success:
            print("  ✅ DELETE do cache funcionando")
        else:
            print("  ❌ DELETE do cache falhou")
            return False
        
        print("✅ Cache Redis funcionando perfeitamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar cache: {e}")
        return False

async def main():
    """Função principal que executa todas as otimizações"""
    print("🚀 Iniciando otimizações de performance do DRE N0...")
    print("=" * 60)
    
    # 1. Testar cache Redis
    cache_ok = await test_cache()
    if not cache_ok:
        print("⚠️ Cache Redis não está funcionando. Continuando com outras otimizações...")
    
    # 2. Criar índices de performance
    indexes_ok = await create_performance_indexes()
    
    # 3. Criar view materializada
    view_ok = await create_materialized_view()
    
    print("=" * 60)
    print("📊 Resumo das otimizações:")
    print(f"  Cache Redis: {'✅' if cache_ok else '❌'}")
    print(f"  Índices: {'✅' if indexes_ok else '❌'}")
    print(f"  View Materializada: {'✅' if view_ok else '❌'}")
    
    if cache_ok and indexes_ok and view_ok:
        print("\n🎉 Todas as otimizações foram aplicadas com sucesso!")
        print("📈 Performance esperada: 70-80% de melhoria")
        print("⏱️ Tempo de resposta: 2-3s → 200-500ms")
    else:
        print("\n⚠️ Algumas otimizações falharam. Verifique os logs acima.")
    
    print("\n🔧 Próximos passos:")
    print("  1. Reiniciar o servidor backend")
    print("  2. Testar endpoints com cache")
    print("  3. Monitorar métricas de performance")

if __name__ == "__main__":
    asyncio.run(main())
