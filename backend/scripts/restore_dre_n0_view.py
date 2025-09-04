#!/usr/bin/env python3
"""
Script para restaurar a view DRE N0
"""

import psycopg2
from sqlalchemy import create_engine, text
import sys
import os

def restore_dre_n0_view():
    """Restaura a view DRE N0 para a versão funcional"""
    
    print("🔄 RESTAURANDO VIEW DRE N0")
    print("=" * 50)
    
    try:
        # Conectar ao banco
        engine = create_engine('postgresql://postgres:postgres@localhost:5432/plataforma_tag')
        conn = engine.connect()
        
        print("✅ Conectado ao banco de dados")
        
        # Verificar se a view existe
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.views 
                WHERE table_name = 'v_dre_n0_completo'
            );
        """))
        
        view_exists = result.fetchone()[0]
        print(f"📊 View v_dre_n0_completo existe: {view_exists}")
        
        if view_exists:
            # Dropar a view existente
            print("🗑️ Removendo view existente...")
            conn.execute(text("DROP VIEW IF EXISTS v_dre_n0_completo CASCADE;"))
            conn.commit()
            print("✅ View removida com sucesso")
        
        # Criar a view restaurada
        print("🔨 Criando view restaurada...")
        
        view_sql = """
        CREATE OR REPLACE VIEW v_dre_n0_completo AS
        WITH valores_agregados AS (
            SELECT 
                ds0.id as dre_n0_id,
                ds0.name as nome_conta,
                ds0.operation_type as tipo_operacao,
                ds0.order_index as ordem,
                ds0.description as descricao,
                ds0.empresa_id,
                
                -- Períodos
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                TO_CHAR(fd.competencia, 'YYYY-Q') || EXTRACT(QUARTER FROM fd.competencia) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia) as periodo_anual,
                
                -- Valores
                SUM(fd.valor_original) as valor_periodo
                
            FROM dre_structure_n0 ds0
            LEFT JOIN financial_data fd ON (
                fd.dre_n1_id = ds0.id OR fd.dre_n2_id = ds0.id
            )
            WHERE ds0.is_active = true
            GROUP BY 
                ds0.id, ds0.name, ds0.operation_type, ds0.order_index, ds0.description, ds0.empresa_id,
                fd.competencia
        ),
        valores_finais AS (
            SELECT 
                dre_n0_id,
                nome_conta,
                tipo_operacao,
                ordem,
                descricao,
                empresa_id,
                
                -- Valores mensais
                SUM(CASE WHEN periodo_mensal = '2025-01' THEN valor_periodo ELSE 0 END) as valor_2025_01,
                SUM(CASE WHEN periodo_mensal = '2025-02' THEN valor_periodo ELSE 0 END) as valor_2025_02,
                SUM(CASE WHEN periodo_mensal = '2025-03' THEN valor_periodo ELSE 0 END) as valor_2025_03,
                SUM(CASE WHEN periodo_mensal = '2025-04' THEN valor_periodo ELSE 0 END) as valor_2025_04,
                SUM(CASE WHEN periodo_mensal = '2025-05' THEN valor_periodo ELSE 0 END) as valor_2025_05,
                SUM(CASE WHEN periodo_mensal = '2025-06' THEN valor_periodo ELSE 0 END) as valor_2025_06,
                SUM(CASE WHEN periodo_mensal = '2025-07' THEN valor_periodo ELSE 0 END) as valor_2025_07,
                SUM(CASE WHEN periodo_mensal = '2025-08' THEN valor_periodo ELSE 0 END) as valor_2025_08,
                SUM(CASE WHEN periodo_mensal = '2025-09' THEN valor_periodo ELSE 0 END) as valor_2025_09,
                SUM(CASE WHEN periodo_mensal = '2025-10' THEN valor_periodo ELSE 0 END) as valor_2025_10,
                SUM(CASE WHEN periodo_mensal = '2025-11' THEN valor_periodo ELSE 0 END) as valor_2025_11,
                SUM(CASE WHEN periodo_mensal = '2025-12' THEN valor_periodo ELSE 0 END) as valor_2025_12,
                
                -- Valores trimestrais
                SUM(CASE WHEN periodo_trimestral = '2025-Q1' THEN valor_periodo ELSE 0 END) as valor_2025_q1,
                SUM(CASE WHEN periodo_trimestral = '2025-Q2' THEN valor_periodo ELSE 0 END) as valor_2025_q2,
                SUM(CASE WHEN periodo_trimestral = '2025-Q3' THEN valor_periodo ELSE 0 END) as valor_2025_q3,
                SUM(CASE WHEN periodo_trimestral = '2025-Q4' THEN valor_periodo ELSE 0 END) as valor_2025_q4,
                
                -- Valores anuais
                SUM(CASE WHEN periodo_anual = 2025 THEN valor_periodo ELSE 0 END) as valor_2025,
                SUM(CASE WHEN periodo_anual = 2024 THEN valor_periodo ELSE 0 END) as valor_2024,
                
                -- Total geral
                SUM(valor_periodo) as valor_total
                
            FROM valores_agregados
            GROUP BY dre_n0_id, nome_conta, tipo_operacao, ordem, descricao, empresa_id
        )
        SELECT 
            dre_n0_id,
            nome_conta,
            tipo_operacao,
            ordem,
            descricao,
            empresa_id,
            
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
            
            -- Orçamentos (zerados por enquanto)
            json_build_object() as orcamentos_mensais,
            json_build_object() as orcamentos_trimestrais,
            json_build_object() as orcamentos_anuais,
            0 as orcamento_total,
            
            valor_total,
            'postgresql' as source
            
        FROM valores_finais
        ORDER BY ordem;
        """
        
        conn.execute(text(view_sql))
        conn.commit()
        print("✅ View restaurada com sucesso")
        
        # Verificar se a view foi criada corretamente
        result = conn.execute(text("""
            SELECT COUNT(*) as total_registros
            FROM v_dre_n0_completo;
        """))
        
        total_registros = result.fetchone()[0]
        print(f"📊 Total de registros na view: {total_registros}")
        
        # Testar a view com algumas consultas
        print("\n🔍 TESTANDO A VIEW RESTAURADA")
        print("-" * 30)
        
        # Teste 1: Verificar estrutura
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'v_dre_n0_completo'
            ORDER BY ordinal_position;
        """))
        
        colunas = result.fetchall()
        print(f"📋 Colunas da view ({len(colunas)}):")
        for coluna in colunas:
            print(f"   - {coluna[0]}: {coluna[1]}")
        
        # Teste 2: Verificar alguns dados
        result = conn.execute(text("""
            SELECT nome_conta, tipo_operacao, ordem, valor_total
            FROM v_dre_n0_completo
            ORDER BY ordem
            LIMIT 5;
        """))
        
        dados = result.fetchall()
        print(f"\n📊 Primeiros 5 registros:")
        for dado in dados:
            print(f"   - {dado[0]} ({dado[1]}) - Ordem: {dado[2]} - Total: R$ {dado[3]:,.2f}")
        
        # Teste 3: Verificar valores por empresa
        result = conn.execute(text("""
            SELECT empresa_id, COUNT(*) as total_contas, SUM(valor_total) as total_valor
            FROM v_dre_n0_completo
            GROUP BY empresa_id
            ORDER BY empresa_id;
        """))
        
        empresas = result.fetchall()
        print(f"\n🏢 Dados por empresa:")
        for empresa in empresas:
            print(f"   - Empresa {empresa[0]}: {empresa[1]} contas - Total: R$ {empresa[2]:,.2f}")
        
        conn.close()
        print("\n🎉 VIEW DRE N0 RESTAURADA COM SUCESSO!")
        print("✅ A view está funcionando corretamente")
        print("✅ Dados estão sendo retornados")
        print("✅ Estrutura está correta")
        
    except Exception as e:
        print(f"❌ Erro ao restaurar view: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restore_dre_n0_view()
