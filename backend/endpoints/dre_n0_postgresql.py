"""
Endpoint para DRE Nível 0 (estrutura principal da aba 'dre') usando PostgreSQL
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
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
                            CONCAT('Q', EXTRACT(QUARTER FROM fd.competencia), '-', EXTRACT(YEAR FROM fd.competencia)) as periodo_trimestral,
                            EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                        FROM financial_data fd
                        WHERE fd.dre_n2 IS NOT NULL 
                        AND fd.dre_n2::text <> '' 
                        AND fd.dre_n2::text <> 'nan'
                        AND fd.valor_original IS NOT NULL 
                        AND fd.competencia IS NOT NULL
                    ),
                    estrutura_n0 AS (
                        -- Estrutura DRE N0 
                        SELECT 
                            ds0.id as dre_n0_id,
                            ds0.name as nome_conta,
                            ds0.operation_type as tipo_operacao,
                            ds0.order_index as ordem,
                            ds0.description as descricao,
                            ds0.dre_niveis,
                            -- Nome para match (apenas para contas não-totalizadoras)
                            CASE 
                                WHEN ds0.operation_type = '=' THEN NULL
                                ELSE ds0.name
                            END as nome_para_match
                        FROM dre_structure_n0 ds0
                        WHERE ds0.is_active = true
                    ),
                    valores_por_periodo AS (
                        -- Valores por todos os períodos para contas não-totalizadoras
                        SELECT 
                            e.dre_n0_id,
                            e.nome_conta,
                            e.tipo_operacao,
                            e.ordem,
                            e.descricao,
                            d.periodo_mensal,
                            d.periodo_trimestral,
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
                                (e.dre_niveis = 'dre_n1' AND d.dre_n1 = e.nome_para_match)
                                OR
                                (e.dre_niveis = 'dre_n2' AND d.dre_n2 = e.nome_para_match)
                            )
                        )
                        WHERE e.tipo_operacao != '='
                        GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, 
                                 d.periodo_mensal, d.periodo_trimestral, d.periodo_anual
                    ),
                    valores_agregados AS (
                        -- Agregar valores por conta e período
                        SELECT 
                            e.dre_n0_id,
                            e.nome_conta,
                            e.tipo_operacao,
                            e.ordem,
                            e.descricao,
                            
                            -- Valores mensais
                            COALESCE(
                                jsonb_object_agg(
                                    vp.periodo_mensal,
                                    vp.valor_calculado
                                ) FILTER (WHERE vp.periodo_mensal IS NOT NULL),
                                '{}'::jsonb
                            ) as valores_mensais,
                            
                            -- Valores trimestrais (preparar para agregação posterior)
                            COALESCE(
                                jsonb_object_agg(
                                    vp.periodo_trimestral,
                                    vp.valor_calculado
                                ) FILTER (WHERE vp.periodo_trimestral IS NOT NULL),
                                '{}'::jsonb
                            ) as valores_trimestrais,
                            
                            -- Valores anuais (preparar para agregação posterior)
                            COALESCE(
                                jsonb_object_agg(
                                    vp.periodo_anual,
                                    vp.valor_calculado
                                ) FILTER (WHERE vp.periodo_anual IS NOT NULL),
                                '{}'::jsonb
                            ) as valores_anuais
                            
                        FROM estrutura_n0 e
                        LEFT JOIN valores_por_periodo vp ON e.dre_n0_id = vp.dre_n0_id
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
                    
                    -- Adicionar contas totalizadoras com valores vazios (serão calculados no código)
                    SELECT 
                        ds0.id as dre_n0_id,
                        ds0.name as nome_conta,
                        ds0.operation_type as tipo_operacao,
                        ds0.order_index as ordem,
                        ds0.description as descricao,
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
                print("✅ View v_dre_n0_completo criada com valores reais e totalizadores")
            
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
                
                dre_item = {
                    "tipo": row.tipo_operacao,
                    "nome": row.nome_conta,
                    "ordem": row.ordem,
                    "expandivel": False,
                    "valores_mensais": valores_mensais_numeros,
                    "valores_trimestrais": valores_trimestrais_numeros,
                    "valores_anuais": valores_anuais_numeros,
                    "orcamentos_mensais": {},
                    "orcamentos_trimestrais": {},
                    "orcamentos_anuais": {},
                    "orcamento_total": 0.0,
                    "classificacoes": []
                }
                
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
                
                # Calcular valores trimestrais (soma dos meses do trimestre)
                for trimestre in trimestres:
                    valor_trimestral = 0.0
                    # Extrair ano e trimestre do formato "Q1-2025"
                    if '-' in trimestre:
                        quarter_part, year_part = trimestre.split('-')
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
                
                # Calcular valores anuais (soma dos meses do ano)
                for ano in anos:
                    valor_anual = 0.0
                    # Somar todos os meses do ano
                    for mes, valor in valores_mensais_calculados.items():
                        if mes.startswith(f'{ano}-'):
                            valor_anual += valor
                    
                    valores_anuais_calculados[ano] = valor_anual
                
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
                    "classificacoes": []
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
