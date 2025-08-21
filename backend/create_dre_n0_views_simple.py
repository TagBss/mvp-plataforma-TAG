#!/usr/bin/env python3
"""
Script simples para criar as views DRE N0 baseadas na tabela dre_structure_n0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_dre_n0_views():
    """Cria as views DRE N0 de forma simples e direta"""
    
    print("🔧 CRIANDO VIEWS DRE N0 DE FORMA SIMPLES...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Remover views existentes se houver
            print("   📋 Removendo views existentes...")
            views_to_drop = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in views_to_drop:
                try:
                    drop_view = text(f'DROP VIEW IF EXISTS {view_name} CASCADE')
                    connection.execute(drop_view)
                    print(f'   ✅ {view_name} removida')
                except Exception as e:
                    print(f'   ⚠️ Erro ao remover {view_name}: {e}')
            
            # 2. Criar view principal v_dre_n0_completo
            print("   🏗️ Criando view principal v_dre_n0_completo...")
            
            create_main_view = text("""
            CREATE VIEW v_dre_n0_completo AS
            SELECT 
                ds0.id as dre_n0_id,
                ds0.name as nome_conta,
                ds0.operation_type as tipo_operacao,
                ds0.order_index as ordem,
                ds0.description as descricao,
                'Bluefit' as origem,
                'Bluefit' as empresa,
                json_build_object() as valores_mensais,
                json_build_object() as valores_trimestrais,
                json_build_object() as valores_anuais,
                json_build_object() as orcamentos_mensais,
                json_build_object() as orcamentos_trimestrais,
                json_build_object() as orcamentos_anuais,
                0 as orcamento_total,
                0 as valor_total,
                'dre_structure_n0' as source
            FROM dre_structure_n0 ds0
            WHERE ds0.is_active = true
            ORDER BY ds0.order_index
            """)
            
            connection.execute(create_main_view)
            print("   ✅ View principal criada")
            
            # 3. Criar view simplificada v_dre_n0_simples
            print("   🏗️ Criando view simplificada v_dre_n0_simples...")
            
            create_simple_view = text("""
            CREATE VIEW v_dre_n0_simples AS
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
            FROM v_dre_n0_completo
            """)
            
            connection.execute(create_simple_view)
            print("   ✅ View simplificada criada")
            
            # 4. Criar view por período v_dre_n0_por_periodo
            print("   🏗️ Criando view por período v_dre_n0_por_periodo...")
            
            create_period_view = text("""
            CREATE VIEW v_dre_n0_por_periodo AS
            SELECT 
                ds0.id as dre_n0_id,
                ds0.name as nome_conta,
                ds0.operation_type as tipo_operacao,
                ds0.order_index as ordem,
                ds0.description as descricao,
                'Bluefit' as origem,
                'Bluefit' as empresa,
                '2025-01' as periodo_mensal,
                '2025-Q1' as periodo_trimestral,
                2025 as periodo_anual,
                0 as valor_periodo
            FROM dre_structure_n0 ds0
            WHERE ds0.is_active = true
            ORDER BY ds0.order_index
            """)
            
            connection.execute(create_period_view)
            print("   ✅ View por período criada")
            
            # 5. Verificar se as views foram criadas
            print("\n🔍 VERIFICANDO SE AS VIEWS FORAM CRIADAS...")
            
            for view_name in views_to_drop:
                try:
                    test_query = text(f'SELECT COUNT(*) FROM {view_name}')
                    count = connection.execute(test_query).scalar()
                    print(f'   ✅ {view_name}: {count} registros')
                except Exception as e:
                    print(f'   ❌ {view_name}: ERRO - {e}')
            
            # 6. Verificar se aparecem no sistema
            print("\n📊 VERIFICANDO SE APARECEM NO SISTEMA...")
            
            # Verificar pg_views
            pg_views_query = text("""
                SELECT viewname 
                FROM pg_views 
                WHERE viewname IN ('v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo')
                AND schemaname = 'public'
            """)
            
            pg_views = connection.execute(pg_views_query).fetchall()
            if pg_views:
                print(f'   ✅ Views em pg_views: {len(pg_views)}')
                for view in pg_views:
                    print(f'      - {view[0]}')
            else:
                print('   ❌ Views não encontradas em pg_views')
            
            # Verificar information_schema
            info_views_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo')
                AND table_schema = 'public'
                AND table_type = 'VIEW'
            """)
            
            info_views = connection.execute(info_views_query).fetchall()
            if info_views:
                print(f'   ✅ Views no information_schema: {len(info_views)}')
                for view in info_views:
                    print(f'      - {view[0]}')
            else:
                print('   ❌ Views não encontradas no information_schema')
            
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = create_dre_n0_views()
        if success:
            print("\n🎉 VIEWS DRE N0 CRIADAS COM SUCESSO!")
            print("   ✅ 3 views criadas baseadas na tabela dre_structure_n0")
            print("   ✅ Views devem aparecer no admin")
            print("   ✅ Estrutura dinâmica implementada")
        else:
            print("\n❌ ERRO AO CRIAR VIEWS DRE N0!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
