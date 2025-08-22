"""
Endpoint para DRE Nível 0 (estrutura principal da aba 'dre') usando PostgreSQL
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from database.connection_sqlalchemy import get_engine
from helpers_postgresql.dre import (
    DreN0Helper, ClassificacoesHelper, PaginationHelper, 
    DebugHelper, PerformanceHelper, get_cache
)
import json
import time
import asyncio

router = APIRouter(prefix="/dre-n0", tags=["dre-n0-postgresql"])

@router.get("/")
async def get_dre_n0(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=10, le=200, description="Itens por página"),
    include_all: bool = Query(False, description="Incluir todos os itens (ignora paginação)")
):
    """Retorna dados da DRE Nível 0 usando a view v_dre_n0_completo com cache Redis e paginação"""
    
    start_time = time.time()
    
    try:
        # Tentar buscar do cache primeiro (se não for paginação)
        cache = await get_cache()
        
        if include_all:
            cache_key = "dre_n0:main"
        else:
            cache_key = f"dre_n0:page_{page}_size_{page_size}"
            
        cached_result = await cache.get(cache_key)
        
        if cached_result:
            print(f"⚡ Cache HIT - DRE N0 retornado em {time.time() - start_time:.3f}s")
            return cached_result
        
        print(f"🔄 Cache MISS - Executando query DRE N0 (página {page}, tamanho {page_size})...")
        
        engine = get_engine()
        
        with engine.connect() as connection:
            # Verificar se a view existe (sem forçar recriação)
            view_exists = DreN0Helper.check_view_exists(connection)
            
            if not view_exists:
                print("🏗️ View DRE N0 não existe, criando...")
                if not DreN0Helper.create_dre_n0_view(connection):
                    raise HTTPException(status_code=500, detail="Erro ao criar view DRE N0")
                print("✅ View v_dre_n0_completo criada com formato correto dos trimestres")
            else:
                print("✅ View DRE N0 já existe, usando view existente")
            
            # Buscar dados da view DRE N0
            rows = DreN0Helper.fetch_dre_n0_data(connection)
            
            if not rows:
                return {
                    "success": False,
                    "message": "Nenhum dado encontrado na view DRE N0",
                    "data": [],
                    "source": "v_dre_n0_completo"
                }
            
            # Processar dados para o formato esperado pelo frontend
            dre_items, meses, trimestres, anos = DreN0Helper.process_dre_items(rows)
            
            # Aplicar paginação se não for include_all
            dados_paginados, pagination_meta = PaginationHelper.apply_pagination_to_dre_items(
                dre_items, page, page_size, include_all
            )
            
            # Ordenar períodos
            meses_ordenados = sorted(list(meses))
            trimestres_ordenados = sorted(list(trimestres))
            anos_ordenados = sorted(list(anos), key=int)
            
            response_data = {
                "success": True,
                "pagination": pagination_meta,
                "meses": meses_ordenados,
                "trimestres": trimestres_ordenados,
                "anos": anos_ordenados,
                "data": dados_paginados,
                "source": f"v_dre_n0_completo - {len(dados_paginados)} contas (página {pagination_meta['current_page']}/{pagination_meta['total_pages']})",
                "total_categorias": pagination_meta['total_items']
            }
            
            # Salvar no cache com TTL de 5 minutos
            await cache.set(cache_key, response_data, ttl=300)
            
            execution_time = time.time() - start_time
            print(f"✅ DRE N0 processada com sucesso: {len(dre_items)} contas em {execution_time:.3f}s")
            return response_data
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar DRE N0: {str(e)}"
        )

@router.get("/simples")
async def get_dre_n0_simples():
    """Retorna dados simplificados da DRE Nível 0"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            query = text("""
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    origem,
                    empresa,
                    valor_total,
                    source
                FROM v_dre_n0_simples
                ORDER BY ordem
            """)
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            return {
                "success": True,
                "data": [
                    {
                        "dre_n0_id": row.dre_n0_id,
                        "nome_conta": row.nome_conta,
                        "tipo_operacao": row.tipo_operacao,
                        "ordem": row.ordem,
                        "descricao": row.descricao,
                        "origem": row.origem,
                        "empresa": row.empresa,
                        "valor_total": float(row.valor_total or 0),
                        "source": row.source
                    }
                    for row in rows
                ],
                "total": len(rows)
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar DRE N0 simples: {str(e)}"
        )

@router.get("/paginated")
async def get_dre_n0_paginated(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=5, le=100, description="Itens por página"),
    search: str = Query(None, description="Termo de busca por nome da conta"),
    order_by: str = Query("ordem", description="Campo para ordenação (ordem, nome, tipo_operacao)")
):
    """Retorna dados da DRE Nível 0 com paginação avançada e busca"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Usar helper de paginação
            dre_items, total_items = PaginationHelper.fetch_paginated_dre_structure(
                connection, page, page_size, search, order_by
            )
            
            # Criar metadados de paginação
            pagination_meta = PaginationHelper.create_pagination_metadata(page, page_size, total_items)
            
            response_data = {
                "success": True,
                "pagination": pagination_meta,
                "data": dre_items,
                "search": search,
                "order_by": order_by,
                "source": f"DRE N0 paginado - {len(dre_items)} contas (página {page}/{pagination_meta['total_pages']})"
            }
            
            return response_data
            
    except Exception as e:
        print(f"❌ Erro na paginação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar DRE N0 paginado: {str(e)}"
        )

@router.get("/por-periodo")
async def get_dre_n0_por_periodo():
    """Retorna dados da DRE Nível 0 organizados por período"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            query = text("""
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    origem,
                    empresa,
                    periodo_mensal,
                    periodo_trimestral,
                    periodo_anual,
                    valor_periodo
                FROM v_dre_n0_por_periodo
                ORDER BY ordem, periodo_mensal
            """)
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            return {
                "success": True,
                "data": [
                    {
                        "dre_n0_id": row.dre_n0_id,
                        "nome_conta": row.nome_conta,
                        "tipo_operacao": row.tipo_operacao,
                        "ordem": row.ordem,
                        "descricao": row.descricao,
                        "origem": row.origem,
                        "empresa": row.empresa,
                        "periodo_mensal": row.periodo_mensal,
                        "periodo_trimestral": row.periodo_trimestral,
                        "periodo_anual": row.periodo_anual,
                        "valor_periodo": float(row.valor_periodo or 0)
                    }
                    for row in rows
                ],
                "total": len(rows)
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar DRE N0 por período: {str(e)}"
        )

@router.get("/recreate-view")
async def recreate_dre_n0_view():
    """Força a recriação da view DRE N0 com correções de agregação e invalida cache"""
    
    try:
        # Invalidar cache antes de recriar view
        cache = await get_cache()
        await cache.invalidate_dre_cache()
        
        engine = get_engine()
        
        with engine.connect() as connection:
            print("🔄 Forçando recriação da view DRE N0 com correções de agregação...")
            
            # Forçar recriação da view
            drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo")
            connection.execute(drop_view)
            
            # Criar view corrigida com agregação correta
            create_view = text("""
                CREATE OR REPLACE VIEW v_dre_n0_completo AS
                WITH dados_limpos AS (
                    -- Filtrar dados válidos da financial_data
                    SELECT 
                        
                        
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                    FROM financial_data fd
                    WHERE  IS NOT NULL 
                    AND ::text <> '' 
                    AND ::text <> 'nan'
                    AND fd.valor_original IS NOT NULL 
                    AND fd.competencia IS NOT NULL
                ),
                estrutura_n0 AS (
                    SELECT 
                        ds0.id as dre_n0_id,
                        ds0.name as nome_conta,
                        ds0.operation_type as tipo_operacao,
                        ds0.order_index as ordem,
                        CASE 
                            WHEN ds0.description LIKE 'Conta DRE N0: %' 
                            THEN SUBSTRING(ds0.description FROM 15)
                            ELSE ds0.description
                        END as descricao,
                        CASE 
                            WHEN ds0.operation_type = '=' THEN NULL
                            ELSE ds0.name
                        END as nome_para_match
                    FROM dre_structure_n0 ds0
                    WHERE ds0.is_active = true
                ),
                valores_mensais AS (
                    -- Valores mensais agregados
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_mensal,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_mensal
                ),
                valores_trimestrais AS (
                    -- Valores trimestrais agregados (soma dos meses)
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_trimestral,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_trimestral
                ),
                valores_anuais AS (
                    -- Valores anuais agregados (soma dos meses)
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_anual,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_anual
                ),
                valores_agregados AS (
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        
                        -- Valores mensais
                        COALESCE(
                            jsonb_object_agg(
                                vm.periodo_mensal,
                                vm.valor_calculado
                            ) FILTER (WHERE vm.periodo_mensal IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_mensais,
                        
                        -- Valores trimestrais
                        COALESCE(
                            jsonb_object_agg(
                                vt.periodo_trimestral,
                                vt.valor_calculado
                            ) FILTER (WHERE vt.periodo_trimestral IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_trimestrais,
                        
                        -- Valores anuais
                        COALESCE(
                            jsonb_object_agg(
                                va.periodo_anual,
                                va.valor_calculado
                            ) FILTER (WHERE va.periodo_anual IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_anuais
                        
                    FROM estrutura_n0 e
                    LEFT JOIN valores_mensais vm ON e.dre_n0_id = vm.dre_n0_id
                    LEFT JOIN valores_trimestrais vt ON e.dre_n0_id = vt.dre_n0_id
                    LEFT JOIN valores_anuais va ON e.dre_n0_id = va.dre_n0_id
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao
                )
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    'CAR' as origem,
                    'BLUEFIT' as empresa,
                    valores_mensais,
                    valores_trimestrais,
                    valores_anuais,
                    '{}'::jsonb as orcamentos_mensais,
                    '{}'::jsonb as orcamentos_trimestrais,
                    '{}'::jsonb as orcamentos_anuais,
                    0 as orcamento_total,
                    0 as valor_total,
                    'v_dre_n0_todos_periodos' as source
                    
                FROM valores_agregados
                
                UNION ALL
                
                -- Adicionar contas totalizadoras com valores vazios
                SELECT 
                    ds0.id as dre_n0_id,
                    ds0.name as nome_conta,
                    ds0.operation_type as tipo_operacao,
                    ds0.order_index as ordem,
                    CASE 
                        WHEN ds0.description LIKE 'Conta DRE N0: %' 
                        THEN SUBSTRING(ds0.description FROM 15)
                        ELSE ds0.description
                    END as descricao,
                    'CAR' as origem,
                    'BLUEFIT' as empresa,
                    '{}'::jsonb as valores_mensais,
                    '{}'::jsonb as valores_trimestrais,
                    '{}'::jsonb as valores_anuais,
                    '{}'::jsonb as orcamentos_mensais,
                    '{}'::jsonb as orcamentos_trimestrais,
                    '{}'::jsonb as orcamentos_anuais,
                    0 as orcamento_total,
                    0 as valor_total,
                    'v_dre_n0_totalizadores' as source
                FROM dre_structure_n0 ds0
                WHERE ds0.is_active = true AND ds0.operation_type = '='
                
                ORDER BY ordem;
            """)
            
            connection.execute(create_view)
            connection.commit()
            
            print("✅ View v_dre_n0_completo recriada com correções de agregação")
            
            return {
                "success": True,
                "message": "View DRE N0 recriada com correções de agregação",
                "correcoes": [
                    "Valores trimestrais agora são agregados corretamente",
                    "Valores anuais agora são agregados corretamente",
                    "Contas DRE N2 agora têm valores corretos para todos os períodos"
                ]
            }
            
    except Exception as e:
        print(f"❌ Erro ao recriar view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao recriar view DRE N0: {str(e)}"
        )

@router.get("/teste-query/{dre_n2_name}")
async def teste_query_classificacoes(dre_n2_name: str):
    """Testa apenas a query SQL das classificações"""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Query simples para testar
            query = text("""
                SELECT DISTINCT classificacao
                FROM financial_data 
                WHERE dre_n2 = :dre_n2_name
                AND classificacao IS NOT NULL 
                AND classificacao::text <> ''
                AND classificacao::text <> 'nan'
                ORDER BY classificacao
                LIMIT 5
            """)
            
            result = connection.execute(query, {"dre_n2_name": dre_n2_name})
            rows = result.fetchall()
            
            return {
                "success": True,
                "message": f"Query executada com sucesso para {dre_n2_name}",
                "total_rows": len(rows),
                "classificacoes": [row.classificacao for row in rows] if rows else []
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro na query: {str(e)}"
        }

@router.get("/teste-conexao")
async def teste_conexao():
    """Testa apenas a conexão com o banco"""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Query simples para testar conexão
            query = text("SELECT 1 as teste")
            result = connection.execute(query)
            row = result.fetchone()
            
            return {
                "success": True,
                "message": "Conexão com banco funcionando",
                "teste": row.teste if row else "N/A"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro na conexão: {str(e)}"
        }

@router.get("/teste-classificacoes")
async def teste_classificacoes():
    """Endpoint de teste para classificações"""
    return {
        "success": True,
        "message": "Endpoint de teste funcionando",
        "data": [
            {
                "tipo": "-",
                "nome": "Teste Classificação",
                "expandivel": False,
                "valores_mensais": {"2025-01": -1000.0},
                "valores_trimestrais": {"2025-Q1": -1000.0},
                "valores_anuais": {"2025": -1000.0},
                "orcamentos_mensais": {},
                "orcamentos_trimestrais": {},
                "orcamentos_anuais": {},
                "orcamento_total": 0.0,
                "classificacoes": []
            }
        ],
        "total_classificacoes": 1
    }

@router.get("/classificacoes/{dre_n2_name}")
async def get_classificacoes_dre_n2(dre_n2_name: str):
    """Retorna as classificações de uma conta DRE N2 específica com cache Redis"""
    
    start_time = time.time()
    print(f"🔍 Buscando classificações para: {dre_n2_name}")
    
    try:
        # Tentar buscar do cache primeiro
        cache = await get_cache()
        cache_key = f"classificacoes:{dre_n2_name}"
        cached_result = await cache.get(cache_key)
        
        if cached_result:
            print(f"⚡ Cache HIT - Classificações retornadas em {time.time() - start_time:.3f}s")
            return cached_result
        
        print(f"🔄 Cache MISS - Executando query classificações...")
        
        engine = get_engine()
        
        with engine.connect() as connection:
            # Usar helper de classificações
            rows = ClassificacoesHelper.fetch_classificacoes_data(connection, dre_n2_name)
            
            if not rows:
                return {
                    "success": False,
                    "message": f"Nenhuma classificação encontrada para {dre_n2_name}",
                    "data": [],
                    "dre_n2": dre_n2_name
                }
            
            # Buscar dados de faturamento para análise vertical
            faturamento_rows = ClassificacoesHelper.fetch_faturamento_data(connection)
            
            # Processar classificações
            classificacoes, meses, trimestres, anos = ClassificacoesHelper.process_classificacoes(rows, faturamento_rows)
            
            # Ordenar períodos
            meses_ordenados = sorted(list(meses))
            trimestres_ordenados = sorted(list(trimestres))
            anos_ordenados = sorted(list(anos))
            
            response_data = {
                "success": True,
                "dre_n2": dre_n2_name,
                "meses": meses_ordenados,
                "trimestres": trimestres_ordenados,
                "anos": anos_ordenados,
                "data": classificacoes,
                "total_classificacoes": len(classificacoes)
            }
            
            # Salvar no cache com TTL de 5 minutos
            await cache.set(cache_key, response_data, ttl=300)
            
            execution_time = time.time() - start_time
            print(f"✅ Classificações processadas com sucesso: {len(classificacoes)} itens em {execution_time:.3f}s")
            return response_data
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar classificações para {dre_n2_name}: {str(e)}"
        )

@router.post("/cache/invalidate")
async def invalidate_cache():
    """Invalida todo o cache relacionado ao DRE"""
    try:
        cache = await get_cache()
        await cache.invalidate_dre_cache()
        return {"success": True, "message": "Cache DRE invalidado com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao invalidar cache: {str(e)}"
        )

@router.get("/cache/status")
async def get_cache_status():
    """Retorna status do cache Redis"""
    try:
        cache = await get_cache()
        if cache.redis:
            info = await cache.redis.info()
            return {
                "success": True,
                "redis_connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
        else:
            return {"success": False, "redis_connected": False}
    except Exception as e:
        return {"success": False, "redis_connected": False, "error": str(e)}

@router.get("/debug/structure")
async def debug_structure():
    """Endpoint de debug para verificar estrutura da tabela"""
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Usar helper de debug
            return DebugHelper.check_table_structure(connection, "dre_structure_n0")
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": str(e.__traceback__)
        }

@router.post("/analytics/pre-calculate")
async def pre_calculate_analytics(
    dre_n2_names: List[str] = Query(..., description="Lista de contas DRE para pré-calcular análises"),
    tipo_periodo: str = Query("mensal", description="Tipo de período (mensal, trimestral, anual)")
):
    """Pré-calcula análises AV/AH para múltiplas contas em lote"""
    try:
        from helpers_postgresql.dre.analytics_cache_helper import get_analytics_cache
        
        analytics_cache = await get_analytics_cache()
        success_count = await analytics_cache.batch_pre_calculate_analytics(dre_n2_names, tipo_periodo)
        
        return {
            "success": True,
            "message": f"Pré-cálculo concluído para {success_count}/{len(dre_n2_names)} contas",
            "total_contas": len(dre_n2_names),
            "sucessos": success_count,
            "tipo_periodo": tipo_periodo
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao pré-calcular análises: {str(e)}"
        )

@router.get("/analytics/{dre_n2_name}")
async def get_analytics(
    dre_n2_name: str,
    tipo_periodo: str = Query("mensal", description="Tipo de período (mensal, trimestral, anual)")
):
    """Retorna análises AV/AH pré-calculadas para uma conta específica"""
    try:
        from helpers_postgresql.dre.analytics_cache_helper import get_analytics_cache
        
        analytics_cache = await get_analytics_cache()
        analytics = await analytics_cache.get_or_calculate_analytics(dre_n2_name, "", tipo_periodo)
        
        if not analytics:
            raise HTTPException(
                status_code=404,
                detail=f"Análises não encontradas para {dre_n2_name}"
            )
        
        return {
            "success": True,
            "data": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar análises: {str(e)}"
        )

@router.post("/analytics/cache/invalidate")
async def invalidate_analytics_cache(dre_n2_name: str = Query(None, description="Conta específica ou todas se não fornecido")):
    """Invalida cache de análises"""
    try:
        from helpers_postgresql.dre.analytics_cache_helper import get_analytics_cache
        
        analytics_cache = await get_analytics_cache()
        await analytics_cache.invalidate_analytics_cache(dre_n2_name)
        
        return {
            "success": True,
            "message": f"Cache de análises invalidado para: {dre_n2_name or 'todas as contas'}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao invalidar cache de análises: {str(e)}"
        )

# ============================================================================
# FASE 3 - NOVOS ENDPOINTS DE PERFORMANCE
# ============================================================================

@router.post("/performance/debounce")
async def debounce_request(
    operation: str = Query(..., description="Nome da operação para debounce"),
    ttl: int = Query(60, description="TTL em segundos para o debounce")
):
    """Implementa debounce para evitar requisições excessivas"""
    try:
        cache_key = f"debounce:{operation}"
        can_proceed = await PerformanceHelper.debounce_request(cache_key, ttl)
        
        return {
            "success": True,
            "can_proceed": can_proceed,
            "operation": operation,
            "ttl": ttl,
            "message": "Requisição permitida" if can_proceed else "Requisição bloqueada por debounce"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no debounce: {str(e)}"
        )

@router.post("/performance/compress")
async def compress_data(
    data: Dict[str, Any],
    compression_ratio: float = Query(0.8, description="Taxa de compressão (0.1 a 1.0)")
):
    """Comprime dados históricos para reduzir tamanho de transferência"""
    try:
        compressed_data = await PerformanceHelper.compress_historical_data(data, compression_ratio)
        
        return {
            "success": True,
            "compression_ratio": compression_ratio,
            "original_size": compressed_data.get('_compression', {}).get('original_size', 0),
            "compressed_size": compressed_data.get('_compression', {}).get('compressed_size', 0),
            "compressed_at": compressed_data.get('_compression', {}).get('compressed_at'),
            "data": compressed_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na compressão: {str(e)}"
        )

@router.get("/performance/metrics")
async def get_performance_metrics(
    operation: str = Query(None, description="Nome da operação específica"),
    date: str = Query(None, description="Data específica (YYYY-MM-DD)")
):
    """Obtém métricas de performance"""
    try:
        metrics = await PerformanceHelper.get_performance_metrics(operation, date)
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        )

@router.post("/performance/optimize")
async def optimize_query_performance(
    query_name: str = Query(..., description="Nome da query para otimizar")
):
    """Otimiza performance de queries específicas"""
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            optimization_result = await PerformanceHelper.optimize_query_performance(connection, query_name)
            
            return {
                "success": True,
                "optimization_result": optimization_result
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na otimização: {str(e)}"
        )

@router.get("/performance/monitor")
async def monitor_performance(
    operation: str = Query(..., description="Nome da operação para monitorar")
):
    """Monitora performance de uma operação específica"""
    try:
        start_time = time.time()
        
        # Simular operação (substituir por operação real)
        await asyncio.sleep(0.1)
        
        metrics = await PerformanceHelper.monitor_performance(operation, start_time)
        
        return {
            "success": True,
            "monitoring_result": metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no monitoramento: {str(e)}"
        )


