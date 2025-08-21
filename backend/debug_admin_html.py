#!/usr/bin/env python3
"""
Script para debugar a geração do HTML da interface admin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def debug_admin_html():
    """Debuga a geração do HTML da interface admin"""
    
    print("🔍 DEBUGANDO GERAÇÃO DO HTML DA INTERFACE ADMIN...")
    
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Simular exatamente o que o admin faz
        print("   📊 1. EXECUTANDO QUERY DO ADMIN:")
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
        print("\n   🔧 2. PROCESSANDO DADOS COMO O ADMIN:")
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
        print(f"\n   📊 3. RESULTADO FINAL:")
        print(f"      📋 Total de itens em table_info: {len(table_info)}")
        
        tables = [t for t in table_info if t['type'] == 'table']
        views = [t for t in table_info if t['type'] == 'view']
        
        print(f"      🔍 Tabelas: {len(tables)}")
        print(f"      📊 Views: {len(views)}")
        
        # 4. Verificar se há problema na lógica de contagem
        print(f"\n   🧮 4. VERIFICANDO LÓGICA DE CONTAGEM:")
        print(f"      📊 Contagem manual de tabelas: {len(tables)}")
        print(f"      📊 Contagem manual de views: {len(views)}")
        
        # 5. Verificar se há problema com tipos
        print(f"\n   🔍 5. VERIFICANDO TIPOS:")
        type_counts = {}
        for item in table_info:
            item_type = item['type']
            if item_type not in type_counts:
                type_counts[item_type] = 0
            type_counts[item_type] += 1
        
        for item_type, count in type_counts.items():
            print(f"      📊 Tipo '{item_type}': {count}")
        
        # 6. Verificar se há problema com a query
        print(f"\n   🔍 6. VERIFICANDO QUERY:")
        print(f"      📋 Query executada: {tables_query.strip()}")
        print(f"      📊 Primeiros 5 resultados:")
        for i, row in enumerate(tables_result[:5]):
            print(f"         {i+1}. {row[0]} ({row[1]})")
        
        # 7. Verificar se há problema com a lógica de renderização
        print(f"\n   🎨 7. VERIFICANDO LÓGICA DE RENDERIZAÇÃO:")
        
        # Simular a lógica de contagem do HTML
        html_tables_count = len([t for t in table_info if t['type'] == 'table'])
        html_views_count = len([t for t in table_info if t['type'] == 'view'])
        
        print(f"      📊 Contagem para HTML - Tabelas: {html_tables_count}")
        print(f"      📊 Contagem para HTML - Views: {html_views_count}")
        
        # 8. Verificar se há problema com os dados
        print(f"\n   🔍 8. VERIFICANDO DADOS:")
        print(f"      📊 Primeiros 3 itens de table_info:")
        for i, item in enumerate(table_info[:3]):
            print(f"         {i+1}. {item['name']} - Tipo: {item['type']} - Count: {item['count']}")
        
        # 9. Verificar se há problema com a estrutura dos dados
        print(f"\n   🔍 9. VERIFICANDO ESTRUTURA DOS DADOS:")
        if table_info:
            first_item = table_info[0]
            print(f"      📊 Primeiro item:")
            print(f"         - Nome: {first_item['name']}")
            print(f"         - Tipo: {first_item['type']}")
            print(f"         - Count: {first_item['count']}")
            print(f"         - Tipo do nome: {type(first_item['name'])}")
            print(f"         - Tipo do tipo: {type(first_item['type'])}")
            print(f"         - Tipo do count: {type(first_item['count'])}")
        
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
        success = debug_admin_html()
        if success:
            print("\n🎯 DEBUG CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO DEBUG!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
