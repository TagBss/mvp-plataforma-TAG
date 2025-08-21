#!/usr/bin/env python3
"""
Script para debugar exatamente o que a query do admin está retornando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def debug_admin_query():
    """Debuga exatamente o que a query do admin está retornando"""
    
    print("🔍 DEBUGANDO QUERY DO ADMIN EXATAMENTE...")
    
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Executar exatamente a mesma query que o admin usa
        print("   📊 1. EXECUTANDO QUERY EXATA DO ADMIN:")
        tables_query = """
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY table_type DESC, table_name
        """
        
        tables_result = session.execute(text(tables_query)).fetchall()
        print(f"   📋 Query retorna: {len(tables_result)} registros")
        
        # 2. Mostrar TODOS os resultados
        print("\n   📋 2. TODOS OS RESULTADOS DA QUERY:")
        for i, row in enumerate(tables_result, 1):
            print(f"      {i:2d}. {row[0]:<30} ({row[1]})")
        
        # 3. Verificar se as views DRE N0 estão na lista
        print("\n   🔍 3. VERIFICANDO VIEWS DRE N0:")
        dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
        
        for view in dre_views:
            found = any(row[0] == view for row in tables_result)
            if found:
                print(f"      ✅ {view}: ENCONTRADA na query")
            else:
                print(f"      ❌ {view}: NÃO encontrada na query")
        
        # 4. Verificar se há algum problema com a sessão
        print("\n   🔧 4. VERIFICANDO SESSÃO:")
        
        # Tentar acessar as views DRE N0 diretamente
        for view in dre_views:
            try:
                count_query = f"SELECT COUNT(*) FROM {view}"
                count = session.execute(text(count_query)).scalar()
                print(f"      ✅ {view}: Acessível via sessão, retorna {count} registros")
            except Exception as e:
                print(f"      ❌ {view}: Erro ao acessar via sessão - {e}")
        
        # 5. Verificar se há problema com a transação
        print("\n   🔧 5. VERIFICANDO TRANSAÇÃO:")
        
        # Verificar se a sessão está ativa
        if session.is_active:
            print("      ✅ Sessão está ativa")
        else:
            print("      ❌ Sessão NÃO está ativa")
        
        # 6. Verificar se há problema com o schema
        print("\n   🔧 6. VERIFICANDO SCHEMA:")
        
        # Verificar se as views existem no schema correto
        for view in dre_views:
            schema_query = text("""
                SELECT table_name, table_schema, table_type
                FROM information_schema.tables 
                WHERE table_name = :view_name
                AND table_schema = 'public'
            """)
            
            result = session.execute(schema_query, {"view_name": view})
            row = result.fetchone()
            
            if row:
                print(f"      ✅ {view}: Encontrada no schema {row[1]} ({row[2]})")
            else:
                print(f"      ❌ {view}: NÃO encontrada no schema public")
        
        # 7. Verificar se há problema com permissões
        print("\n   🔧 7. VERIFICANDO PERMISSÕES:")
        
        # Verificar permissões do usuário atual
        permissions_query = text("""
            SELECT current_user, current_database(), current_schema()
        """)
        
        result = session.execute(permissions_query)
        user_info = result.fetchone()
        
        print(f"      📊 Usuário atual: {user_info[0]}")
        print(f"      📊 Banco atual: {user_info[1]}")
        print(f"      📊 Schema atual: {user_info[2]}")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    try:
        success = debug_admin_query()
        if success:
            print("\n🎯 DEBUG CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO DEBUG!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
