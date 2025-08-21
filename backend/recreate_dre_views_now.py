#!/usr/bin/env python3
"""
Script para recriar as views DRE N0 agora e verificar se elas persistem
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
import time

def recreate_dre_views_now():
    """Recria as views DRE N0 agora e verifica se elas persistem"""
    
    print("🔄 RECRIANDO VIEWS DRE N0 AGORA...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar estado inicial
            print("\n📋 1. ESTADO INICIAL:")
            initial_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_type = 'VIEW' 
                AND table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = connection.execute(initial_query)
            initial_views = result.fetchall()
            
            print(f"   📊 Views existentes: {len(initial_views)}")
            for view in initial_views:
                print(f"      - {view[0]} ({view[1]})")
            
            # 2. Recriar v_dre_n0_completo
            print("\n🔄 2. CRIANDO v_dre_n0_completo:")
            
            create_completo_query = text("""
            CREATE OR REPLACE VIEW v_dre_n0_completo AS
            SELECT 
                ds0.id as dre_n0_id,
                ds0.name as nome_conta,
                ds0.operation_type as tipo_operacao,
                ds0.order_index as ordem,
                ds0.description as descricao,
                'Bluefit' as origem,
                'Bluefit' as empresa,
                '{}'::json as valores_mensais,
                '{}'::json as valores_trimestrais,
                '{}'::json as valores_anuais,
                '{}'::json as orcamentos_mensais,
                '{}'::json as orcamentos_trimestrais,
                '{}'::json as orcamentos_anuais,
                0 as orcamento_total,
                0 as valor_total,
                'dre_structure_n0' as source
            FROM dre_structure_n0 ds0
            WHERE ds0.is_active = true
            ORDER BY ds0.order_index
            """)
            
            try:
                connection.execute(create_completo_query)
                print("   ✅ v_dre_n0_completo: Criada com sucesso")
            except Exception as e:
                print(f"   ❌ v_dre_n0_completo: {e}")
                return False
            
            # 3. Recriar v_dre_n0_simples
            print("\n🔄 3. CRIANDO v_dre_n0_simples:")
            
            create_simples_query = text("""
            CREATE OR REPLACE VIEW v_dre_n0_simples AS
            SELECT 
                dre_n0_id,
                nome_conta,
                tipo_operacao,
                ordem,
                valor_total
            FROM v_dre_n0_completo
            ORDER BY ordem
            """)
            
            try:
                connection.execute(create_simples_query)
                print("   ✅ v_dre_n0_simples: Criada com sucesso")
            except Exception as e:
                print(f"   ❌ v_dre_n0_simples: {e}")
                return False
            
            # 4. Recriar v_dre_n0_por_periodo
            print("\n🔄 4. CRIANDO v_dre_n0_por_periodo:")
            
            create_periodo_query = text("""
            CREATE OR REPLACE VIEW v_dre_n0_por_periodo AS
            SELECT 
                dre_n0_id,
                nome_conta,
                tipo_operacao,
                ordem,
                valores_mensais,
                valores_trimestrais,
                valores_anuais
            FROM v_dre_n0_completo
            ORDER BY ordem
            """)
            
            try:
                connection.execute(create_periodo_query)
                print("   ✅ v_dre_n0_por_periodo: Criada com sucesso")
            except Exception as e:
                print(f"   ❌ v_dre_n0_por_periodo: {e}")
                return False
            
            # 5. Verificar se as views foram criadas
            print("\n🔍 5. VERIFICANDO VIEWS CRIADAS:")
            
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in dre_views:
                check_query = text(f"""
                    SELECT COUNT(*) as total 
                    FROM information_schema.tables 
                    WHERE table_name = '{view_name}' 
                    AND table_schema = 'public'
                """)
                
                result = connection.execute(check_query)
                exists = result.scalar() > 0
                
                if exists:
                    print(f"   ✅ {view_name}: CRIADA COM SUCESSO")
                    
                    # Testar se a view retorna dados
                    try:
                        test_query = text(f"SELECT COUNT(*) as total FROM {view_name}")
                        result = connection.execute(test_query)
                        count = result.scalar()
                        print(f"      📊 Retorna {count} registros")
                    except Exception as e:
                        print(f"      ❌ Erro ao testar: {e}")
                else:
                    print(f"   ❌ {view_name}: NÃO FOI CRIADA")
            
            # 6. Aguardar um pouco e verificar novamente
            print("\n⏳ 6. AGUARDANDO E VERIFICANDO NOVAMENTE:")
            print("   ⏰ Aguardando 5 segundos...")
            time.sleep(5)
            
            # Verificar novamente se as views ainda existem
            final_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_type = 'VIEW' 
                AND table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = connection.execute(final_query)
            final_views = result.fetchall()
            
            print(f"   📊 Views após 5 segundos: {len(final_views)}")
            for view in final_views:
                print(f"      - {view[0]} ({view[1]})")
            
            # 7. Verificar se as views DRE N0 ainda estão lá
            print("\n🔍 7. VERIFICANDO PERSISTÊNCIA DAS VIEWS DRE N0:")
            
            for view_name in dre_views:
                still_exists = any(view[0] == view_name for view in final_views)
                if still_exists:
                    print(f"   ✅ {view_name}: AINDA EXISTE após 5 segundos")
                else:
                    print(f"   ❌ {view_name}: DESAPARECEU após 5 segundos")
            
            # 8. Verificar se as views aparecem na interface admin
            print("\n🌐 8. VERIFICANDO VISIBILIDADE NA INTERFACE ADMIN:")
            
            admin_query = text("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY table_type DESC, table_name
            """)
            
            result = connection.execute(admin_query)
            admin_tables = result.fetchall()
            
            tables_count = len([t for t in admin_tables if t[1] == 'BASE TABLE'])
            views_count = len([t for t in admin_tables if t[1] == 'VIEW'])
            
            print(f"   📊 Admin encontra: {tables_count} tabelas e {views_count} views")
            
            # Verificar se as views DRE N0 estão na lista
            for view_name in dre_views:
                found = any(t[0] == view_name for t in admin_tables)
                if found:
                    print(f"   ✅ {view_name}: encontrada pelo admin!")
                else:
                    print(f"   ❌ {view_name}: NÃO encontrada pelo admin")
            
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = recreate_dre_views_now()
        if success:
            print("\n🎯 VIEWS DRE N0 RECRIADAS COM SUCESSO!")
        else:
            print("\n❌ ERRO AO RECRIAR VIEWS!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
