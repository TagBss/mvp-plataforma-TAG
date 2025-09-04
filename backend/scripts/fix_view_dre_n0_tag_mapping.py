#!/usr/bin/env python3
"""
Script para corrigir a view DRE N0 com mapeamento correto para TAG
Corrige o JOIN de_para -> plano_de_contas removendo prefixo [ código ]
"""

import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text

def fix_view_dre_n0_tag_mapping():
    """Corrige a view DRE N0 para mapear corretamente dados da TAG"""
    
    print("🔧 CORRIGINDO VIEW DRE N0 - MAPEAMENTO TAG")
    print("=" * 60)
    
    with DatabaseSession() as session:
        # 1. Criar backup da view atual
        print("\n1️⃣ CRIANDO BACKUP DA VIEW ATUAL")
        print("-" * 40)
        
        session.execute(text("""
            CREATE OR REPLACE VIEW v_dre_n0_completo_backup AS
            SELECT * FROM v_dre_n0_completo
        """))
        print("✅ Backup criado: v_dre_n0_completo_backup")
        
        # 2. Recriar view com JOIN corrigido
        print("\n2️⃣ RECRIANDO VIEW COM JOIN CORRIGIDO")
        print("-" * 40)
        
        session.execute(text("DROP VIEW IF EXISTS v_dre_n0_completo CASCADE"))
        
        # View corrigida com JOIN que remove prefixo [ código ]
        create_view_sql = """
        CREATE OR REPLACE VIEW v_dre_n0_completo AS
        WITH dados_limpos AS (
            -- Filtrar dados válidos usando fluxo correto: financial_data -> de_para -> plano_de_contas
            SELECT 
                fd.id,
                fd.classificacao,
                fd.valor_original,
                fd.competencia,
                fd.empresa_id,
                e.nome as empresa_nome,
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                pc.classificacao_dre_n2,
                pc.classificacao_dfc_n2
            FROM financial_data fd
            JOIN empresas e ON fd.empresa_id = e.id
            JOIN de_para dp ON fd.de_para_id = dp.id
            JOIN plano_de_contas pc ON (
                -- JOIN CORRIGIDO: Remove prefixo [ código ] do de_para
                TRIM(SUBSTRING(dp.descricao_destino FROM '\\] (.+)$')) = pc.nome_conta
                OR dp.descricao_destino = pc.nome_conta  -- Fallback para casos sem prefixo
            )
            WHERE fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            AND pc.classificacao_dre_n2 IS NOT NULL
        ),
        estrutura_n0 AS (
            SELECT 
                ds0.id as dre_n0_id,
                ds0.name as nome_conta,
                ds0.operation_type as tipo_operacao,
                ds0.order_index as ordem,
                ds0.description as descricao
            FROM dre_structure_n0 ds0
            WHERE ds0.is_active = true
        ),
        valores_agregados AS (
            -- Agregar valores por conta DRE N0
            SELECT 
                e.dre_n0_id,
                e.nome_conta,
                e.tipo_operacao,
                e.ordem,
                e.descricao,
                d.empresa_nome,
                d.periodo_mensal,
                d.periodo_trimestral,
                d.periodo_anual,
                CASE 
                    WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                    WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                    WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                    ELSE SUM(d.valor_original)
                END as valor_calculado
            FROM estrutura_n0 e
            LEFT JOIN dados_limpos d ON (
                -- Mapear classificacao_dre_n2 para estrutura DRE N0
                d.classificacao_dre_n2 LIKE '%' || e.nome_conta || '%'
                OR e.nome_conta LIKE '%' || d.classificacao_dre_n2 || '%'
            )
            GROUP BY 
                e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao,
                d.empresa_nome, d.periodo_mensal, d.periodo_trimestral, d.periodo_anual
        ),
        valores_finais AS (
            SELECT 
                dre_n0_id,
                nome_conta,
                tipo_operacao,
                ordem,
                descricao,
                empresa_nome,
                
                -- Valores mensais
                SUM(CASE WHEN periodo_mensal = '2025-01' THEN valor_calculado ELSE 0 END) as valor_2025_01,
                SUM(CASE WHEN periodo_mensal = '2025-02' THEN valor_calculado ELSE 0 END) as valor_2025_02,
                SUM(CASE WHEN periodo_mensal = '2025-03' THEN valor_calculado ELSE 0 END) as valor_2025_03,
                SUM(CASE WHEN periodo_mensal = '2025-04' THEN valor_calculado ELSE 0 END) as valor_2025_04,
                SUM(CASE WHEN periodo_mensal = '2025-05' THEN valor_calculado ELSE 0 END) as valor_2025_05,
                SUM(CASE WHEN periodo_mensal = '2025-06' THEN valor_calculado ELSE 0 END) as valor_2025_06,
                SUM(CASE WHEN periodo_mensal = '2025-07' THEN valor_calculado ELSE 0 END) as valor_2025_07,
                SUM(CASE WHEN periodo_mensal = '2025-08' THEN valor_calculado ELSE 0 END) as valor_2025_08,
                SUM(CASE WHEN periodo_mensal = '2025-09' THEN valor_calculado ELSE 0 END) as valor_2025_09,
                SUM(CASE WHEN periodo_mensal = '2025-10' THEN valor_calculado ELSE 0 END) as valor_2025_10,
                SUM(CASE WHEN periodo_mensal = '2025-11' THEN valor_calculado ELSE 0 END) as valor_2025_11,
                SUM(CASE WHEN periodo_mensal = '2025-12' THEN valor_calculado ELSE 0 END) as valor_2025_12,
                
                -- Valores trimestrais
                SUM(CASE WHEN periodo_trimestral = '2025-Q1' THEN valor_calculado ELSE 0 END) as valor_2025_q1,
                SUM(CASE WHEN periodo_trimestral = '2025-Q2' THEN valor_calculado ELSE 0 END) as valor_2025_q2,
                SUM(CASE WHEN periodo_trimestral = '2025-Q3' THEN valor_calculado ELSE 0 END) as valor_2025_q3,
                SUM(CASE WHEN periodo_trimestral = '2025-Q4' THEN valor_calculado ELSE 0 END) as valor_2025_q4,
                
                -- Valores anuais
                SUM(CASE WHEN periodo_anual = '2025' THEN valor_calculado ELSE 0 END) as valor_2025,
                SUM(CASE WHEN periodo_anual = '2024' THEN valor_calculado ELSE 0 END) as valor_2024,
                
                -- Total geral
                SUM(valor_calculado) as valor_total
                
            FROM valores_agregados
            GROUP BY dre_n0_id, nome_conta, tipo_operacao, ordem, descricao, empresa_nome
        )
        SELECT 
            dre_n0_id,
            nome_conta,
            tipo_operacao,
            ordem,
            descricao,
            empresa_nome as empresa,
            'CAP' as origem,  -- Default para origem
            
            -- Valores mensais como JSON
            json_build_object(
                '2025-01', valor_2025_01,
                '2025-02', valor_2025_02,
                '2025-03', valor_2025_03,
                '2025-04', valor_2025_04,
                '2025-05', valor_2025_05,
                '2025-06', valor_2025_06,
                '2025-07', valor_2025_07,
                '2025-08', valor_2025_08,
                '2025-09', valor_2025_09,
                '2025-10', valor_2025_10,
                '2025-11', valor_2025_11,
                '2025-12', valor_2025_12
            ) as valores_mensais,
            
            -- Valores trimestrais como JSON
            json_build_object(
                '2025-Q1', valor_2025_q1,
                '2025-Q2', valor_2025_q2,
                '2025-Q3', valor_2025_q3,
                '2025-Q4', valor_2025_q4
            ) as valores_trimestrais,
            
            -- Valores anuais como JSON
            json_build_object(
                '2025', valor_2025,
                '2024', valor_2024
            ) as valores_anuais,
            
            -- Orçamentos (zerados)
            json_build_object() as orcamentos_mensais,
            json_build_object() as orcamentos_trimestrais,
            json_build_object() as orcamentos_anuais,
            0 as orcamento_total,
            
            valor_total,
            'CAP' as source
            
        FROM valores_finais
        ORDER BY ordem;
        """
        
        session.execute(text(create_view_sql))
        print("✅ View recriada com JOIN corrigido")
        
        # 3. Testar a view
        print("\n3️⃣ TESTANDO A VIEW CORRIGIDA")
        print("-" * 40)
        
        result = session.execute(text("""
            SELECT 
                empresa,
                COUNT(*) as total_contas,
                SUM(valor_total) as valor_total_geral
            FROM v_dre_n0_completo 
            WHERE valor_total != 0
            GROUP BY empresa
            ORDER BY empresa
        """))
        
        print("Resultados por empresa:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} contas, R$ {row[2]:,.2f}")
        
        # 4. Verificar especificamente TAG Business Solutions
        print("\n4️⃣ VERIFICANDO TAG BUSINESS SOLUTIONS")
        print("-" * 40)
        
        result = session.execute(text("""
            SELECT 
                nome_conta,
                valor_total,
                valores_mensais
            FROM v_dre_n0_completo 
            WHERE empresa = 'TAG Business Solutions'
            AND valor_total != 0
            ORDER BY ABS(valor_total) DESC
            LIMIT 10
        """))
        
        print("Top 10 contas TAG Business Solutions:")
        for row in result:
            print(f"  - {row[0]}: R$ {row[1]:,.2f}")
        
        print("\n✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)

if __name__ == "__main__":
    fix_view_dre_n0_tag_mapping()
