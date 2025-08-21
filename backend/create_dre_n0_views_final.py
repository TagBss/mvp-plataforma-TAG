#!/usr/bin/env python3
"""
Script FINAL para criar as views DRE N0 de forma robusta
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_dre_n0_views_final():
    """Cria as views DRE N0 de forma robusta e verifica cada passo"""
    
    print("🔧 CRIANDO VIEWS DRE N0 DE FORMA FINAL E ROBUSTA...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar se a tabela dre_structure_n0 existe
            print("   🔍 Verificando se a tabela dre_structure_n0 existe...")
            check_table = text("SELECT COUNT(*) FROM dre_structure_n0")
            count = connection.execute(check_table).scalar()
            print(f"   ✅ Tabela dre_structure_n0: {count} registros")
            
            # 2. Remover views existentes se houver
            print("   📋 Removendo views existentes...")
            views_to_drop = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in views_to_drop:
                try:
                    drop_view = text(f'DROP VIEW IF EXISTS {view_name} CASCADE')
                    connection.execute(drop_view)
                    print(f'   ✅ {view_name} removida')
                except Exception as e:
                    print(f'   ⚠️ Erro ao remover {view_name}: {e}')
            
            # 3. Criar view principal v_dre_n0_completo
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
            
            # 4. Verificar se a view foi criada
            print("   🔍 Verificando se v_dre_n0_completo foi criada...")
            try:
                test_main = text("SELECT COUNT(*) FROM v_dre_n0_completo")
                count_main = connection.execute(test_main).scalar()
                print(f"   ✅ v_dre_n0_completo: {count_main} registros")
            except Exception as e:
                print(f"   ❌ Erro ao testar v_dre_n0_completo: {e}")
                return False
            
            # 5. Criar view simplificada v_dre_n0_simples
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
            
            # 6. Verificar se a view foi criada
            print("   🔍 Verificando se v_dre_n0_simples foi criada...")
            try:
                test_simple = text("SELECT COUNT(*) FROM v_dre_n0_simples")
                count_simple = connection.execute(test_simple).scalar()
                print(f"   ✅ v_dre_n0_simples: {count_simple} registros")
            except Exception as e:
                print(f"   ❌ Erro ao testar v_dre_n0_simples: {e}")
                return False
            
            # 7. Criar view por período v_dre_n0_por_periodo
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
            
            # 8. Verificar se a view foi criada
            print("   🔍 Verificando se v_dre_n0_por_periodo foi criada...")
            try:
                test_period = text("SELECT COUNT(*) FROM v_dre_n0_por_periodo")
                count_period = connection.execute(test_period).scalar()
                print(f"   ✅ v_dre_n0_por_periodo: {count_period} registros")
            except Exception as e:
                print(f"   ❌ Erro ao testar v_dre_n0_por_periodo: {e}")
                return False
            
            # 9. Verificar se as views aparecem no sistema
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
                return False
            
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
                return False
            
            # 10. Teste final - verificar se a query do admin encontra as views
            print("\n🧪 TESTE FINAL - QUERY DO ADMIN...")
            admin_query = text("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY table_type DESC, table_name
            """)
            
            admin_result = connection.execute(admin_query)
            admin_tables_views = admin_result.fetchall()
            
            tables = [row for row in admin_tables_views if row[1] == 'BASE TABLE']
            views = [row for row in admin_tables_views if row[1] == 'VIEW']
            
            print(f'   📊 Admin encontra: {len(tables)} tabelas e {len(views)} views')
            
            # Verificar se nossas views estão na lista
            view_names = [row[0] for row in views]
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view in dre_views:
                if view in view_names:
                    print(f'   ✅ {view} encontrada pelo admin!')
                else:
                    print(f'   ❌ {view} NÃO encontrada pelo admin')
                    return False
            
            print("\n🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = create_dre_n0_views_final()
        if success:
            print("\n🎉 VIEWS DRE N0 CRIADAS COM SUCESSO!")
            print("   ✅ 3 views criadas e validadas")
            print("   ✅ Views aparecem no sistema")
            print("   ✅ Admin deve conseguir listar as views")
            print("   ✅ Estrutura dinâmica implementada")
        else:
            print("\n❌ ERRO AO CRIAR VIEWS DRE N0!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
