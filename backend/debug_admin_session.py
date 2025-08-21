#!/usr/bin/env python3
"""
Script para debugar a sessão do admin e identificar por que as views DRE N0 não estão sendo renderizadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def debug_admin_session():
    """Debuga a sessão do admin para identificar o problema"""
    
    print("🔍 DEBUGANDO SESSÃO DO ADMIN...")
    
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Simular exatamente o que o admin faz
        print("   📊 1. SIMULANDO ADMIN EXATAMENTE:")
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
        
        # 3. Processar os dados como o admin faz
        print("\n   🔧 3. PROCESSANDO DADOS COMO O ADMIN:")
        table_info = []
        
        for row in tables_result:
            table_name = row[0]
            table_type = "table" if row[1] == "BASE TABLE" else "view"
            
            print(f"      - {table_name} ({table_type})")
            
            try:
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = session.execute(text(count_query)).scalar()
                table_info.append({"name": table_name, "count": count, "type": table_type})
                print(f"        ✅ Contagem: {count}")
            except Exception as e:
                table_info.append({"name": table_name, "count": f"Erro: {e}", "type": table_type})
                print(f"        ❌ Erro: {e}")
        
        # 4. Verificar o resultado final
        print(f"\n   📊 4. RESULTADO FINAL:")
        print(f"      📋 Total de itens em table_info: {len(table_info)}")
        
        tables = [t for t in table_info if t['type'] == 'table']
        views = [t for t in table_info if t['type'] == 'view']
        
        print(f"      🔍 Tabelas: {len(tables)}")
        print(f"      📊 Views: {len(views)}")
        
        # 5. Verificar se as views DRE N0 estão na lista
        print(f"\n   🔍 5. VERIFICANDO VIEWS DRE N0:")
        dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
        
        for view in dre_views:
            found = False
            for item in table_info:
                if item['name'] == view:
                    found = True
                    print(f"      ✅ {view}: {item['count']} registros ({item['type']})")
                    break
            if not found:
                print(f"      ❌ {view}: NÃO ENCONTRADA")
        
        # 6. Verificar se há problema com a sessão
        print(f"\n   🔧 6. VERIFICANDO SESSÃO:")
        
        # Verificar se a sessão está ativa
        if session.is_active:
            print("      ✅ Sessão está ativa")
        else:
            print("      ❌ Sessão NÃO está ativa")
        
        # Verificar se há problema com a transação
        try:
            # Tentar fazer uma query simples
            test_query = text("SELECT 1 as test")
            result = session.execute(test_query)
            test_result = result.scalar()
            print(f"      ✅ Query de teste funcionou: {test_result}")
        except Exception as e:
            print(f"      ❌ Query de teste falhou: {e}")
        
        # 7. Verificar se há problema com as views DRE N0 especificamente
        print(f"\n   🔧 7. VERIFICANDO VIEWS DRE N0 ESPECIFICAMENTE:")
        
        for view in dre_views:
            try:
                # Verificar se a view existe
                exists_query = text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = '{view}' 
                    AND table_schema = 'public'
                """)
                
                result = session.execute(exists_query)
                exists = result.scalar() > 0
                
                if exists:
                    print(f"      ✅ {view}: Existe no information_schema")
                    
                    # Tentar acessar a view
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {view}")
                        count = session.execute(count_query).scalar()
                        print(f"         📊 Acessível, retorna {count} registros")
                    except Exception as e:
                        print(f"         ❌ Erro ao acessar: {e}")
                else:
                    print(f"      ❌ {view}: NÃO existe no information_schema")
                    
            except Exception as e:
                print(f"      ❌ {view}: Erro ao verificar - {e}")
        
        # 8. Verificar se há problema com a ordem das views
        print(f"\n   🔧 8. VERIFICANDO ORDEM DAS VIEWS:")
        
        # Verificar se as views DRE N0 estão sendo filtradas por algum motivo
        for i, row in enumerate(tables_result):
            if row[1] == 'VIEW':
                print(f"      {i+1}. {row[0]} (VIEW)")
                if row[0] in dre_views:
                    print(f"         🎯 ENCONTRADA: {row[0]}")
        
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
        success = debug_admin_session()
        if success:
            print("\n🎯 DEBUG CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO DEBUG!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
