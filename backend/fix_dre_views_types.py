#!/usr/bin/env python3
"""
Script corrigido para recriar views DRE N0 com tipos de dados corretos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def fix_dre_views_types():
    """Recria views DRE N0 com tipos de dados corretos"""
    
    print("🔧 RECRIANDO VIEWS DRE N0 COM TIPOS CORRETOS...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar views existentes
            print("\n📋 1. VERIFICANDO VIEWS EXISTENTES:")
            views_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_type = 'VIEW' 
                AND table_schema = 'public'
                ORDER BY table_name
            """)
            
            result = connection.execute(views_query)
            existing_views = result.fetchall()
            
            print(f"   📊 Total de views encontradas: {len(existing_views)}")
            for view in existing_views:
                print(f"      - {view[0]} ({view[1]})")
            
            # 2. Drop views DRE N0 se existirem
            print("\n🗑️ 2. REMOVENDO VIEWS DRE N0 EXISTENTES:")
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in dre_views:
                try:
                    drop_query = text(f"DROP VIEW IF EXISTS {view_name} CASCADE")
                    connection.execute(drop_query)
                    print(f"   ✅ {view_name}: Removida")
                except Exception as e:
                    print(f"   ⚠️ {view_name}: {e}")
            
            # 3. Criar v_dre_n0_completo com tipos corretos
            print("\n🔄 3. CRIANDO v_dre_n0_completo:")
            
            create_completo_query = text("""
            CREATE VIEW v_dre_n0_completo AS
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
            
            # 4. Criar v_dre_n0_simples
            print("\n🔄 4. CRIANDO v_dre_n0_simples:")
            
            create_simples_query = text("""
            CREATE VIEW v_dre_n0_simples AS
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
            
            # 5. Criar v_dre_n0_por_periodo
            print("\n🔄 5. CRIANDO v_dre_n0_por_periodo:")
            
            create_periodo_query = text("""
            CREATE VIEW v_dre_n0_por_periodo AS
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
            
            # 6. Verificar se as views foram criadas
            print("\n🔍 6. VERIFICANDO VIEWS CRIADAS:")
            
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
                        
                        # Ver dados de exemplo
                        if count > 0:
                            sample_query = text(f"SELECT nome_conta, tipo_operacao, ordem FROM {view_name} LIMIT 3")
                            result = connection.execute(sample_query)
                            samples = result.fetchall()
                            print(f"      📋 Exemplos:")
                            for sample in samples:
                                print(f"         - {sample[0]} ({sample[1]}) - Ordem: {sample[2]}")
                    except Exception as e:
                        print(f"      ❌ Erro ao testar: {e}")
                else:
                    print(f"   ❌ {view_name}: NÃO FOI CRIADA")
            
            # 7. Verificar se as views aparecem na interface admin
            print("\n🌐 7. VERIFICANDO VISIBILIDADE NA INTERFACE ADMIN:")
            
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
        success = fix_dre_views_types()
        if success:
            print("\n🎯 VIEWS DRE N0 RECRIADAS COM SUCESSO!")
        else:
            print("\n❌ ERRO AO RECRIAR VIEWS!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
