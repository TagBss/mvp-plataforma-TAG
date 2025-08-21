#!/usr/bin/env python3
"""
Script simples para verificar o status real das views DRE N0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def check_views_status():
    """Verifica o status real das views DRE N0"""
    
    print("🔍 VERIFICANDO STATUS REAL DAS VIEWS DRE N0...")
    
    # Criar nova conexão
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar se conseguimos acessar as views diretamente
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view_name in dre_views:
                try:
                    test_query = text(f'SELECT COUNT(*) FROM {view_name}')
                    count = connection.execute(test_query).scalar()
                    print(f'   ✅ {view_name}: {count} registros (FUNCIONANDO)')
                except Exception as e:
                    print(f'   ❌ {view_name}: ERRO - {e}')
            
            # 2. Verificar todas as views existentes no sistema
            print('\n📋 TODAS AS VIEWS EXISTENTES:')
            all_views_query = text('''
                SELECT schemaname, viewname 
                FROM pg_views 
                WHERE schemaname = 'public'
                ORDER BY viewname
            ''')
            
            all_views = connection.execute(all_views_query).fetchall()
            if all_views:
                for view in all_views:
                    print(f'   - {view[1]} (schema: {view[0]})')
            else:
                print('   ❌ Nenhuma view encontrada em pg_views')
            
            # 3. Verificar se há views em information_schema.views
            print('\n📊 VIEWS NO INFORMATION_SCHEMA:')
            info_views_query = text('''
                SELECT table_schema, table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name
            ''')
            
            info_views = connection.execute(info_views_query).fetchall()
            if info_views:
                for view in info_views:
                    print(f'   - {view[1]} (schema: {view[0]})')
            else:
                print('   ❌ Nenhuma view encontrada em information_schema.views')
                
    except Exception as e:
        print(f'❌ Erro na conexão: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_views_status()
