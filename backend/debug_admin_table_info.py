#!/usr/bin/env python3
"""
Script para debugar o problema da interface admin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def debug_admin_table_info():
    """Debuga o problema da interface admin"""
    
    print("🔍 DEBUGANDO PROBLEMA DA INTERFACE ADMIN...")
    
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Executar a mesma query que o admin usa
        print("   📊 Executando query do admin...")
        tables_query = """
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY table_type DESC, table_name
        """
        
        tables_result = session.execute(text(tables_query)).fetchall()
        print(f"   📋 Query retorna: {len(tables_result)} registros")
        
        # 2. Processar os dados como o admin faz
        print("   🔧 Processando dados como o admin...")
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
        
        # 3. Verificar o resultado final
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   📋 Total de itens em table_info: {len(table_info)}")
        
        tables = [t for t in table_info if t['type'] == 'table']
        views = [t for t in table_info if t['type'] == 'view']
        
        print(f"   🔍 Tabelas: {len(tables)}")
        print(f"   📊 Views: {len(views)}")
        
        # 4. Verificar se nossas views estão na lista
        print(f"\n🔍 VERIFICANDO VIEWS DRE N0:")
        dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
        
        for view in dre_views:
            found = False
            for item in table_info:
                if item['name'] == view:
                    found = True
                    print(f"   ✅ {view}: {item['count']} registros ({item['type']})")
                    break
            if not found:
                print(f"   ❌ {view}: NÃO ENCONTRADA")
        
        # 5. Verificar se há problema na lógica de contagem
        print(f"\n🧮 VERIFICANDO LÓGICA DE CONTAGEM:")
        print(f"   📊 Contagem manual de tabelas: {len(tables)}")
        print(f"   📊 Contagem manual de views: {len(views)}")
        
        # 6. Verificar se há problema com tipos
        print(f"\n🔍 VERIFICANDO TIPOS:")
        type_counts = {}
        for item in table_info:
            item_type = item['type']
            if item_type not in type_counts:
                type_counts[item_type] = 0
            type_counts[item_type] += 1
        
        for item_type, count in type_counts.items():
            print(f"   📊 Tipo '{item_type}': {count}")
        
        # 7. Verificar se há problema com a query
        print(f"\n🔍 VERIFICANDO QUERY:")
        print(f"   📋 Query executada: {tables_query.strip()}")
        print(f"   📊 Primeiros 5 resultados:")
        for i, row in enumerate(tables_result[:5]):
            print(f"      {i+1}. {row[0]} ({row[1]})")
        
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
        success = debug_admin_table_info()
        if success:
            print("\n🎯 DEBUG CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO DEBUG!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
