#!/usr/bin/env python3
"""
Script para verificar se as views DRE N0 realmente existem no banco
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def check_views_existence():
    """Verifica se as views DRE N0 realmente existem no banco"""
    
    print("🔍 VERIFICANDO EXISTÊNCIA DAS VIEWS DRE N0...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar todas as views no banco
            print("\n📋 1. VERIFICANDO TODAS AS VIEWS NO BANCO:")
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
            
            # 2. Verificar especificamente as views DRE N0
            print("\n🔍 2. VERIFICANDO VIEWS DRE N0 ESPECIFICAMENTE:")
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in dre_views:
                # Verificar se existe na information_schema
                schema_query = text("""
                    SELECT table_name, table_schema, table_type
                    FROM information_schema.tables 
                    WHERE table_name = :view_name
                    AND table_schema = 'public'
                """)
                
                result = connection.execute(schema_query, {"view_name": view_name})
                row = result.fetchone()
                
                if row:
                    print(f"   ✅ {view_name}: Encontrada no information_schema")
                    
                    # Tentar acessar a view
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {view_name}")
                        count = connection.execute(count_query).scalar()
                        print(f"      📊 Acessível, retorna {count} registros")
                    except Exception as e:
                        print(f"      ❌ Erro ao acessar: {e}")
                else:
                    print(f"   ❌ {view_name}: NÃO encontrada no information_schema")
            
            # 3. Verificar se há views com nomes similares
            print("\n🔍 3. VERIFICANDO VIEWS COM NOMES SIMILARES:")
            similar_views_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_type = 'VIEW' 
                AND table_schema = 'public'
                AND table_name LIKE '%dre%' OR table_name LIKE '%n0%'
                ORDER BY table_name
            """)
            
            result = connection.execute(similar_views_query)
            similar_views = result.fetchall()
            
            if similar_views:
                print("   📊 Views com nomes similares:")
                for view in similar_views:
                    print(f"      - {view[0]} ({view[1]})")
            else:
                print("   📊 Nenhuma view com nome similar encontrada")
            
            # 4. Verificar se as views foram dropadas
            print("\n🔍 4. VERIFICANDO SE AS VIEWS FORAM DROPADAS:")
            
            # Verificar se há algum problema com as views
            for view_name in dre_views:
                try:
                    # Tentar criar uma view simples para testar
                    test_view_query = text(f"""
                        CREATE OR REPLACE VIEW {view_name}_test AS
                        SELECT 1 as test
                    """)
                    connection.execute(test_view_query)
                    
                    # Se chegou aqui, a view foi criada com sucesso
                    print(f"   ✅ {view_name}: Pode ser criada (teste bem-sucedido)")
                    
                    # Remover a view de teste
                    drop_test_query = text(f"DROP VIEW IF EXISTS {view_name}_test")
                    connection.execute(drop_test_query)
                    
                except Exception as e:
                    print(f"   ❌ {view_name}: Erro ao criar view de teste - {e}")
            
            # 5. Verificar se há problema com permissões
            print("\n🔍 5. VERIFICANDO PERMISSÕES:")
            
            # Verificar usuário atual
            user_query = text("SELECT current_user, current_database()")
            result = connection.execute(user_query)
            user_info = result.fetchone()
            
            print(f"   📊 Usuário atual: {user_info[0]}")
            print(f"   📊 Banco atual: {user_info[1]}")
            
            # Verificar se o usuário tem permissão para criar views
            try:
                test_perm_query = text("""
                    CREATE OR REPLACE VIEW test_permission AS
                    SELECT 1 as test
                """)
                connection.execute(test_perm_query)
                
                # Se chegou aqui, tem permissão
                print("   ✅ Usuário tem permissão para criar views")
                
                # Remover view de teste
                drop_perm_query = text("DROP VIEW IF EXISTS test_permission")
                connection.execute(drop_perm_query)
                
            except Exception as e:
                print(f"   ❌ Usuário NÃO tem permissão para criar views: {e}")
            
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = check_views_existence()
        if success:
            print("\n🎯 VERIFICAÇÃO CONCLUÍDA!")
        else:
            print("\n❌ ERRO NA VERIFICAÇÃO!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
