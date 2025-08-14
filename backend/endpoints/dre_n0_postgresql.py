"""
Endpoint para DRE Nível 0 (estrutura principal da aba 'dre') usando PostgreSQL
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from database.connection_sqlalchemy import get_engine
import json

router = APIRouter(prefix="/dre-n0", tags=["DRE Nível 0"])

@router.get("/")
async def get_dre_n0():
    """Retorna dados da DRE Nível 0 usando a view v_dre_n0_completo"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Primeiro, verificar se a view existe, se não, criar
            check_view = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_views WHERE viewname = 'v_dre_n0_completo'
                )
            """)
            
            result = connection.execute(check_view)
            view_exists = result.scalar()
            
            if not view_exists:
                print("🏗️ View DRE N0 não existe, criando...")
                
                # Forçar recriação da view com formato correto dos trimestres
                drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo")
                connection.execute(drop_view)
                
                # Criar view corrigida com lógica de totalizadores e todos os períodos
                create_view = text("""
                    CREATE OR REPLACE VIEW v_dre_n0_completo AS
                    WITH dados_limpos AS (
                        -- Filtrar dados válidos da financial_data
                        SELECT 
                            fd.dre_n2,
                            fd.dre_n1,
                            fd.competencia,
                            fd.valor_original,
                            TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                            CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                            EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                        FROM financial_data fd
                        WHERE fd.dre_n2 IS NOT NULL 
                        AND fd.dre_n2::text <> '' 
                        AND fd.dre_n2::text <> 'nan'
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
                print("✅ View v_dre_n0_completo criada com formato correto dos trimestres")
            else:
                print("🔄 View DRE N0 já existe, forçando recriação para aplicar correções...")
                
                # Forçar recriação da view com formato correto dos trimestres
                drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo")
                connection.execute(drop_view)
                
                # Criar view corrigida com lógica de totalizadores e todos os períodos
                create_view = text("""
                    CREATE OR REPLACE VIEW v_dre_n0_completo AS
                    WITH dados_limpos AS (
                        -- Filtrar dados válidos da financial_data
                        SELECT 
                            fd.dre_n2,
                            fd.dre_n1,
                            fd.competencia,
                            fd.valor_original,
                            TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                            CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                            EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                        FROM financial_data fd
                        WHERE fd.dre_n2 IS NOT NULL 
                        AND fd.dre_n2::text <> '' 
                        AND fd.dre_n2::text <> 'nan'
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
                print("✅ View v_dre_n0_completo recriada com formato correto dos trimestres")
            
            # Buscar dados da view DRE N0
            query = text("""
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    origem,
                    empresa,
                    valores_mensais,
                    valores_trimestrais,
                    valores_anuais,
                    orcamentos_mensais,
                    orcamentos_trimestrais,
                    orcamentos_anuais,
                    orcamento_total,
                    valor_total,
                    source
                FROM v_dre_n0_completo
                ORDER BY ordem
            """)
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return {
                    "success": False,
                    "message": "Nenhum dado encontrado na view DRE N0",
                    "data": [],
                    "source": "v_dre_n0_completo"
                }
            
            # Processar dados para o formato esperado pelo frontend
            dre_items = []
            meses = set()
            trimestres = set()
            anos = set()
            
            # Separar valores reais e totalizadores
            valores_reais = []
            totalizadores = []
            
            for row in rows:
                if row.tipo_operacao == '=':
                    totalizadores.append(row)
                else:
                    valores_reais.append(row)
            
            # Processar valores reais primeiro
            valores_reais_por_periodo = {}
            for row in valores_reais:
                valores_mensais = row.valores_mensais or {}
                valores_trimestrais = row.valores_trimestrais or {}
                valores_anuais = row.valores_anuais or {}
                
                meses.update(valores_mensais.keys())
                trimestres.update(valores_trimestrais.keys())
                anos.update(valores_anuais.keys())
                
                valores_mensais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_mensais.items()}
                valores_trimestrais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_trimestrais.items()}
                valores_anuais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_anuais.items()}
                
                # Verificar se a conta tem classificações (é expansível)
                tem_classificacoes = False
                # Verificar se existem classificações na tabela financial_data para qualquer conta
                check_classificacoes = text("""
                    SELECT COUNT(*) FROM financial_data 
                    WHERE dre_n2 = :dre_n2_name 
                    AND classificacao IS NOT NULL 
                    AND classificacao::text <> '' 
                    AND classificacao::text <> 'nan'
                """)
                result_check = connection.execute(check_classificacoes, {"dre_n2_name": row.nome_conta})
                count_classificacoes = result_check.scalar()
                tem_classificacoes = count_classificacoes > 0
                
                # VALIDAÇÃO: Garantir que todos os períodos tenham valores (mesmo que zero)
                for periodo in meses:
                    if periodo not in valores_mensais_numeros:
                        valores_mensais_numeros[periodo] = 0.0
                
                for trimestre in trimestres:
                    if trimestre not in valores_trimestrais_numeros:
                        valores_trimestrais_numeros[trimestre] = 0.0
                
                for ano in anos:
                    if ano not in valores_anuais_numeros:
                        valores_anuais_numeros[ano] = 0.0
                
                dre_item = {
                    "tipo": row.tipo_operacao,
                    "nome": row.nome_conta,
                    "ordem": row.ordem,
                    "expandivel": tem_classificacoes,
                    "valores_mensais": valores_mensais_numeros,
                    "valores_trimestrais": valores_trimestrais_numeros,
                    "valores_anuais": valores_anuais_numeros,
                    "orcamentos_mensais": {},
                    "orcamentos_trimestrais": {},
                    "orcamentos_anuais": {},
                    "orcamento_total": 0.0,
                    "classificacoes": [],
                    # Análise Horizontal e Vertical para contas reais
                    "analise_horizontal_mensal": {},
                    "analise_vertical_mensal": {},
                    "analise_horizontal_trimestral": {},
                    "analise_vertical_trimestral": {},
                    "analise_horizontal_anual": {},
                    "analise_vertical_anual": {}
                }
                
                # Calcular Análise Horizontal e Vertical para contas reais
                for periodo in valores_mensais_numeros:
                    # Análise Vertical (representatividade sobre Faturamento)
                    faturamento_periodo = 0.0
                    for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                        if 'Faturamento' in dados['nome']:
                            faturamento_periodo = dados['valor']
                            break
                    
                    if faturamento_periodo > 0:
                        dre_item["analise_vertical_mensal"][periodo] = (valores_mensais_numeros[periodo] / faturamento_periodo) * 100
                    else:
                        dre_item["analise_vertical_mensal"][periodo] = 0.0
                    
                    # Análise Horizontal (variação vs período anterior)
                    if len(valores_mensais_numeros) > 1:
                        meses_ordenados = sorted(list(valores_mensais_numeros.keys()))
                        indice_atual = meses_ordenados.index(periodo)
                        if indice_atual > 0:
                            periodo_anterior = meses_ordenados[indice_atual - 1]
                            valor_anterior = valores_mensais_numeros.get(periodo_anterior, 0.0)
                            if valor_anterior != 0:
                                variacao = ((valores_mensais_numeros[periodo] - valor_anterior) / valor_anterior) * 100
                                dre_item["analise_horizontal_mensal"][periodo] = variacao
                            else:
                                dre_item["analise_horizontal_mensal"][periodo] = 0.0
                        else:
                            dre_item["analise_horizontal_mensal"][periodo] = 0.0
                    else:
                        dre_item["analise_horizontal_mensal"][periodo] = 0.0
                
                # Calcular AH e AV para trimestres
                for trimestre in valores_trimestrais_numeros:
                    # Análise Vertical trimestral
                    faturamento_trimestral = 0.0
                    for mes in valores_mensais_numeros:
                        if mes.startswith(trimestre.split('-')[0]):  # Mesmo ano
                            for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                                if 'Faturamento' in dados['nome']:
                                    faturamento_trimestral += dados['valor']
                    
                    if faturamento_trimestral > 0:
                        dre_item["analise_vertical_trimestral"][trimestre] = (valores_trimestrais_numeros[trimestre] / faturamento_trimestral) * 100
                    else:
                        dre_item["analise_vertical_trimestral"][trimestre] = 0.0
                    
                    # Análise Horizontal trimestral
                    if len(valores_trimestrais_numeros) > 1:
                        trimestres_ordenados = sorted(list(valores_trimestrais_numeros.keys()))
                        indice_atual = trimestres_ordenados.index(trimestre)
                        if indice_atual > 0:
                            trimestre_anterior = trimestres_ordenados[indice_atual - 1]
                            valor_anterior = valores_trimestrais_numeros.get(trimestre_anterior, 0.0)
                            if valor_anterior != 0:
                                variacao = ((valores_trimestrais_numeros[trimestre] - valor_anterior) / valor_anterior) * 100
                                dre_item["analise_horizontal_trimestral"][trimestre] = variacao
                            else:
                                dre_item["analise_horizontal_trimestral"][trimestre] = 0.0
                        else:
                            dre_item["analise_horizontal_trimestral"][trimestre] = 0.0
                    else:
                        dre_item["analise_horizontal_trimestral"][trimestre] = 0.0
                
                # Calcular AH e AV para anos
                for ano in valores_anuais_numeros:
                    # Análise Vertical anual
                    faturamento_anual = 0.0
                    for mes in valores_mensais_numeros:
                        if mes.startswith(ano):
                            for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                                if 'Faturamento' in dados['nome']:
                                    faturamento_anual += dados['valor']
                    
                    if faturamento_anual > 0:
                        dre_item["analise_vertical_anual"][ano] = (valores_anuais_numeros[ano] / faturamento_anual) * 100
                    else:
                        dre_item["analise_vertical_anual"][ano] = 0.0
                    
                    # Análise Horizontal anual
                    if len(anos) > 1:
                        anos_ordenados = sorted([int(a) for a in anos])
                        indice_atual = anos_ordenados.index(int(ano))
                        if indice_atual > 0:
                            ano_anterior = anos_ordenados[indice_atual - 1]
                            valor_anterior = valores_anuais_numeros.get(str(ano_anterior), 0.0)
                            if valor_anterior != 0:
                                variacao = ((valores_anuais_numeros[ano] - valor_anterior) / valor_anterior) * 100
                                dre_item["analise_horizontal_anual"][ano] = variacao
                            else:
                                dre_item["analise_horizontal_anual"][ano] = 0.0
                        else:
                            dre_item["analise_horizontal_anual"][ano] = 0.0
                    else:
                        dre_item["analise_horizontal_anual"][ano] = 0.0
                
                dre_items.append(dre_item)
                
                # Armazenar para cálculo dos totalizadores
                for periodo, valor in valores_mensais_numeros.items():
                    if periodo not in valores_reais_por_periodo:
                        valores_reais_por_periodo[periodo] = {}
                    valores_reais_por_periodo[periodo][row.ordem] = {
                        'valor': valor,
                        'tipo': row.tipo_operacao,
                        'nome': row.nome_conta
                    }
            
            # Agora calcular e adicionar totalizadores
            for tot in totalizadores:
                valores_mensais_calculados = {}
                valores_trimestrais_calculados = {}
                valores_anuais_calculados = {}
                
                # Análise Horizontal e Vertical
                analise_horizontal_mensal = {}
                analise_vertical_mensal = {}
                analise_horizontal_trimestral = {}
                analise_vertical_trimestral = {}
                analise_horizontal_anual = {}
                analise_vertical_anual = {}
                
                # Calcular valores mensais dos totalizadores
                for periodo in meses:
                    valor_calculado = 0.0
                    
                    # Lógica específica para cada totalizador
                    if 'Receita Bruta' in tot.nome_conta:
                        # Receita Bruta = Faturamento
                        for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                            if ordem < tot.ordem and 'Faturamento' in dados['nome']:
                                valor_calculado += dados['valor']
                                
                    elif 'Receita Líquida' in tot.nome_conta:
                        # Receita Líquida = Receita Bruta + Tributos (tributos são negativos)
                        for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                            if ordem < tot.ordem and dados['tipo'] in ['+', '-']:
                                valor_calculado += dados['valor']
                                
                    elif 'Resultado Bruto' in tot.nome_conta:
                        # Resultado Bruto = Receita Líquida - CMV - CSP - CPV
                        for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                            if ordem < tot.ordem and dados['tipo'] in ['+', '-']:
                                valor_calculado += dados['valor']
                                
                    else:
                        # Outros totalizadores: somar tudo anterior
                        for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                            if ordem < tot.ordem and dados['tipo'] in ['+', '-', '+/-']:
                                valor_calculado += dados['valor']
                    
                    valores_mensais_calculados[periodo] = valor_calculado
                    
                    # Calcular Análise Vertical (representatividade sobre Faturamento)
                    faturamento_periodo = 0.0
                    for ordem, dados in valores_reais_por_periodo.get(periodo, {}).items():
                        if 'Faturamento' in dados['nome']:
                            faturamento_periodo = dados['valor']
                            break
                    
                    if faturamento_periodo > 0:
                        analise_vertical_mensal[periodo] = (valor_calculado / faturamento_periodo) * 100
                    else:
                        analise_vertical_mensal[periodo] = 0.0
                    
                    # Calcular Análise Horizontal (variação vs período anterior)
                    if len(meses) > 1:
                        meses_ordenados = sorted(list(meses))
                        indice_atual = meses_ordenados.index(periodo)
                        if indice_atual > 0:
                            periodo_anterior = meses_ordenados[indice_atual - 1]
                            valor_anterior = valores_mensais_calculados.get(periodo_anterior, 0.0)
                            if valor_anterior != 0:
                                variacao = ((valor_calculado - valor_anterior) / valor_anterior) * 100
                                analise_horizontal_mensal[periodo] = variacao
                            else:
                                analise_horizontal_mensal[periodo] = 0.0
                        else:
                            analise_horizontal_mensal[periodo] = 0.0
                    else:
                        analise_horizontal_mensal[periodo] = 0.0
                
                # Calcular valores trimestrais (soma dos meses do trimestre)
                for trimestre in trimestres:
                    valor_trimestral = 0.0
                    # Extrair ano e trimestre do formato "2025-Q1"
                    if '-' in trimestre:
                        year_part, quarter_part = trimestre.split('-')
                        quarter_num = quarter_part.replace('Q', '')
                        
                        # Meses do trimestre
                        meses_trimestre = []
                        if quarter_num == '1':
                            meses_trimestre = [f'{year_part}-01', f'{year_part}-02', f'{year_part}-03']
                        elif quarter_num == '2':
                            meses_trimestre = [f'{year_part}-04', f'{year_part}-05', f'{year_part}-06']
                        elif quarter_num == '3':
                            meses_trimestre = [f'{year_part}-07', f'{year_part}-08', f'{year_part}-09']
                        elif quarter_num == '4':
                            meses_trimestre = [f'{year_part}-10', f'{year_part}-11', f'{year_part}-12']
                        
                        # Somar valores dos meses do trimestre
                        for mes in meses_trimestre:
                            if mes in valores_mensais_calculados:
                                valor_trimestral += valores_mensais_calculados[mes]
                    
                    valores_trimestrais_calculados[trimestre] = valor_trimestral
                    
                    # Calcular Análise Vertical trimestral
                    faturamento_trimestral = 0.0
                    for mes in meses_trimestre:
                        for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                            if 'Faturamento' in dados['nome']:
                                faturamento_trimestral += dados['valor']
                    
                    if faturamento_trimestral > 0:
                        analise_vertical_trimestral[trimestre] = (valor_trimestral / faturamento_trimestral) * 100
                    else:
                        analise_vertical_trimestral[trimestre] = 0.0
                    
                    # Calcular Análise Horizontal trimestral
                    if len(trimestres) > 1:
                        trimestres_ordenados = sorted(list(trimestres))
                        indice_atual = trimestres_ordenados.index(trimestre)
                        if indice_atual > 0:
                            trimestre_anterior = trimestres_ordenados[indice_atual - 1]
                            valor_anterior = valores_trimestrais_calculados.get(trimestre_anterior, 0.0)
                            if valor_anterior != 0:
                                variacao = ((valor_trimestral - valor_anterior) / valor_anterior) * 100
                                analise_horizontal_trimestral[trimestre] = variacao
                            else:
                                analise_horizontal_trimestral[trimestre] = 0.0
                        else:
                            analise_horizontal_trimestral[trimestre] = 0.0
                    else:
                        analise_horizontal_trimestral[trimestre] = 0.0
                
                # Calcular valores anuais (soma dos meses do ano)
                for ano in anos:
                    valor_anual = 0.0
                    # Somar todos os meses do ano
                    for mes, valor in valores_mensais_calculados.items():
                        if mes.startswith(f'{ano}-'):
                            valor_anual += valor
                    
                    valores_anuais_calculados[ano] = valor_anual
                    
                    # Calcular Análise Vertical anual
                    faturamento_anual = 0.0
                    for mes, valor in valores_mensais_calculados.items():
                        if mes.startswith(f'{ano}-'):
                            for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                                if 'Faturamento' in dados['nome']:
                                    faturamento_anual += dados['valor']
                    
                    if faturamento_anual > 0:
                        analise_vertical_anual[ano] = (valor_anual / faturamento_anual) * 100
                    else:
                        analise_vertical_anual[ano] = 0.0
                    
                    # Calcular Análise Horizontal anual
                    if len(anos) > 1:
                        anos_ordenados = sorted([int(a) for a in anos])
                        indice_atual = anos_ordenados.index(int(ano))
                        if indice_atual > 0:
                            ano_anterior = anos_ordenados[indice_atual - 1]
                            valor_anterior = valores_anuais_calculados.get(str(ano_anterior), 0.0)
                            if valor_anterior != 0:
                                variacao = ((valor_anual - valor_anterior) / valor_anterior) * 100
                                analise_horizontal_anual[ano] = variacao
                            else:
                                analise_horizontal_anual[ano] = 0.0
                        else:
                            analise_horizontal_anual[ano] = 0.0
                    else:
                        analise_horizontal_anual[ano] = 0.0
                
                # VALIDAÇÃO: Garantir que todos os períodos tenham valores (mesmo que zero)
                for periodo in meses:
                    if periodo not in valores_mensais_calculados:
                        valores_mensais_calculados[periodo] = 0.0
                        analise_horizontal_mensal[periodo] = 0.0
                        analise_vertical_mensal[periodo] = 0.0
                
                for trimestre in trimestres:
                    if trimestre not in valores_trimestrais_calculados:
                        valores_trimestrais_calculados[trimestre] = 0.0
                        analise_horizontal_trimestral[trimestre] = 0.0
                        analise_vertical_trimestral[trimestre] = 0.0
                
                for ano in anos:
                    if ano not in valores_anuais_calculados:
                        valores_anuais_calculados[ano] = 0.0
                        analise_horizontal_anual[ano] = 0.0
                        analise_vertical_anual[ano] = 0.0
                
                # Adicionar totalizador à lista
                dre_item_tot = {
                    "tipo": tot.tipo_operacao,
                    "nome": tot.nome_conta,
                    "ordem": tot.ordem,
                    "expandivel": False,
                    "valores_mensais": valores_mensais_calculados,
                    "valores_trimestrais": valores_trimestrais_calculados,
                    "valores_anuais": valores_anuais_calculados,
                    "orcamentos_mensais": {},
                    "orcamentos_trimestrais": {},
                    "orcamentos_anuais": {},
                    "orcamento_total": 0.0,
                    "classificacoes": [],
                    # Análise Horizontal e Vertical
                    "analise_horizontal_mensal": analise_horizontal_mensal,
                    "analise_vertical_mensal": analise_vertical_mensal,
                    "analise_horizontal_trimestral": analise_horizontal_trimestral,
                    "analise_vertical_trimestral": analise_vertical_trimestral,
                    "analise_horizontal_anual": analise_horizontal_anual,
                    "analise_vertical_anual": analise_vertical_anual
                }
                
                dre_items.append(dre_item_tot)
            
            # Ordenar por ordem
            dre_items.sort(key=lambda x: x.get('ordem', 0))
            
            # Ordenar períodos
            meses_ordenados = sorted(list(meses))
            trimestres_ordenados = sorted(list(trimestres))
            anos_ordenados = sorted(list(anos), key=int)
            
            return {
                "success": True,
                "meses": meses_ordenados,
                "trimestres": trimestres_ordenados,
                "anos": anos_ordenados,
                "data": dre_items,
                "source": f"v_dre_n0_completo - {len(dre_items)} contas",
                "total_categorias": len(dre_items)
            }
            
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
    """Força a recriação da view DRE N0 com correções de agregação"""
    
    try:
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
                        fd.dre_n2,
                        fd.dre_n1,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                    FROM financial_data fd
                    WHERE fd.dre_n2 IS NOT NULL 
                    AND fd.dre_n2::text <> '' 
                    AND fd.dre_n2::text <> 'nan'
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
    """Retorna as classificações de uma conta DRE N2 específica"""
    
    print(f"🔍 Buscando classificações para: {dre_n2_name}")
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Query para buscar classificações com valores para todos os períodos
            query = text("""
                SELECT 
                    fd.classificacao,
                    fd.valor_original,
                    TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                    CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                    EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                FROM financial_data fd
                WHERE fd.dre_n2 = :dre_n2_name
                AND fd.classificacao IS NOT NULL 
                AND fd.classificacao::text <> ''
                AND fd.classificacao::text <> 'nan'
                AND fd.valor_original IS NOT NULL 
                AND fd.competencia IS NOT NULL
                ORDER BY fd.classificacao, fd.competencia
            """)
            
            result = connection.execute(query, {"dre_n2_name": dre_n2_name})
            rows = result.fetchall()
            
            if not rows:
                return {
                    "success": False,
                    "message": f"Nenhuma classificação encontrada para {dre_n2_name}",
                    "data": [],
                    "dre_n2": dre_n2_name
                }
            
            # Agrupar dados por classificação
            dados_por_classificacao = {}
            meses = set()
            trimestres = set()
            anos = set()
            
            for row in rows:
                nome_classificacao = row.classificacao
                periodo_mensal = row.periodo_mensal
                periodo_trimestral = row.periodo_trimestral
                periodo_anual = row.periodo_anual
                valor = float(row.valor_original) if row.valor_original is not None else 0.0
                
                if nome_classificacao not in dados_por_classificacao:
                    dados_por_classificacao[nome_classificacao] = {
                        'mensais': {},
                        'trimestrais': {},
                        'anuais': {},
                        'valor_total': 0.0
                    }
                
                # Adicionar valor ao período mensal
                if periodo_mensal:
                    if periodo_mensal in dados_por_classificacao[nome_classificacao]['mensais']:
                        dados_por_classificacao[nome_classificacao]['mensais'][periodo_mensal] += valor
                    else:
                        dados_por_classificacao[nome_classificacao]['mensais'][periodo_mensal] = valor
                    meses.add(periodo_mensal)
                
                # Adicionar valor ao período trimestral
                if periodo_trimestral:
                    if periodo_trimestral in dados_por_classificacao[nome_classificacao]['trimestrais']:
                        dados_por_classificacao[nome_classificacao]['trimestrais'][periodo_trimestral] += valor
                    else:
                        dados_por_classificacao[nome_classificacao]['trimestrais'][periodo_trimestral] = valor
                    trimestres.add(periodo_trimestral)
                
                # Adicionar valor ao período anual
                if periodo_anual:
                    if periodo_anual in dados_por_classificacao[nome_classificacao]['anuais']:
                        dados_por_classificacao[nome_classificacao]['anuais'][periodo_anual] += valor
                    else:
                        dados_por_classificacao[nome_classificacao]['anuais'][periodo_anual] = valor
                    anos.add(periodo_anual)
                
                # Acumular valor total
                dados_por_classificacao[nome_classificacao]['valor_total'] += valor
            
            # Criar itens de classificação
            classificacoes = []
            for nome_classificacao, dados in dados_por_classificacao.items():
                # Determinar tipo baseado no valor total (se é negativo ou positivo)
                tipo_classificacao = "-" if dados['valor_total'] < 0 else "+"
                
                print(f"  📝 Criando classificação: {nome_classificacao}, valor_total: {dados['valor_total']}, tipo: {tipo_classificacao}")
                
                classificacao_item = {
                    "tipo": tipo_classificacao,  # Tipo baseado no valor real
                    "nome": nome_classificacao,
                    "expandivel": False,
                    "valores_mensais": dados['mensais'],
                    "valores_trimestrais": dados['trimestrais'],  # Agora com valores trimestrais
                    "valores_anuais": dados['anuais'],           # Agora com valores anuais
                    "orcamentos_mensais": {},
                    "orcamentos_trimestrais": {},
                    "orcamentos_anuais": {},
                    "orcamento_total": 0.0,
                    "classificacoes": []
                }
                
                classificacoes.append(classificacao_item)
            
            # Ordenar períodos
            meses_ordenados = sorted(list(meses))
            trimestres_ordenados = sorted(list(trimestres))
            anos_ordenados = sorted(list(anos))
            
            return {
                "success": True,
                "dre_n2": dre_n2_name,
                "meses": meses_ordenados,
                "trimestres": trimestres_ordenados,
                "anos": anos_ordenados,
                "data": classificacoes,
                "total_classificacoes": len(classificacoes)
            }
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar classificações para {dre_n2_name}: {str(e)}"
        )


