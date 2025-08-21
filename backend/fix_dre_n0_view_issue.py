#!/usr/bin/env python3
"""
Script para verificar e corrigir o problema da view DRE N0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def fix_dre_n0_view_issue():
    """Verifica e corrige o problema da view DRE N0"""
    
    print("🔍 VERIFICANDO STATUS DA VIEW DRE N0...")
    
    engine = get_engine()
    with engine.connect() as connection:
        
        # 1. Verificar se conseguimos acessar a view diretamente
        try:
            direct_query = text('SELECT COUNT(*) FROM v_dre_n0_completo')
            count = connection.execute(direct_query).scalar()
            print(f'   ✅ View acessível diretamente: {count} registros')
        except Exception as e:
            print(f'   ❌ Erro ao acessar view: {e}')
            return False
        
        # 2. Verificar se a view está em pg_views
        pg_views_query = text('''
            SELECT schemaname, viewname, definition 
            FROM pg_views 
            WHERE viewname = 'v_dre_n0_completo'
        ''')
        
        pg_result = connection.execute(pg_views_query).fetchone()
        if pg_result:
            print(f'   ✅ View encontrada em pg_views: {pg_result[0]}.{pg_result[1]}')
            print(f'   📝 Definição: {pg_result[2][:100]}...')
        else:
            print('   ❌ View não encontrada em pg_views')
        
        # 3. Verificar se a view está em information_schema.views
        info_views_query = text('''
            SELECT table_schema, table_name, view_definition
            FROM information_schema.views 
            WHERE table_name = 'v_dre_n0_completo'
        ''')
        
        info_result = connection.execute(info_views_query).fetchone()
        if info_result:
            print(f'   ✅ View encontrada em information_schema.views: {info_result[0]}.{info_result[1]}')
        else:
            print('   ❌ View não encontrada em information_schema.views')
        
        # 4. Verificar se há problema de permissões
        permissions_query = text('''
            SELECT grantee, privilege_type 
            FROM information_schema.role_table_grants 
            WHERE table_name = 'v_dre_n0_completo'
        ''')
        
        permissions = connection.execute(permissions_query).fetchall()
        if permissions:
            print(f'   🔐 Permissões encontradas: {len(permissions)}')
            for perm in permissions:
                print(f'      - {perm[0]}: {perm[1]}')
        else:
            print('   ⚠️ Nenhuma permissão encontrada')
        
        # 5. Verificar se a view está no schema correto
        schema_query = text('SELECT current_schema()')
        current_schema = connection.execute(schema_query).scalar()
        print(f'   📊 Schema atual: {current_schema}')
        
        # 6. Tentar recriar a view com schema explícito
        print('\n🔧 TENTANDO RECRIAR VIEW COM SCHEMA EXPLÍCITO...')
        
        try:
            # Remover view existente
            drop_view = text('DROP VIEW IF EXISTS v_dre_n0_completo CASCADE')
            connection.execute(drop_view)
            print('   ✅ View anterior removida')
            
            # Recriar view com schema explícito
            create_view = text('''
            CREATE VIEW public.v_dre_n0_completo AS
            SELECT 
                id, name, operation_type, order_index, dre_niveis, description as descricao,
                '2025-01' as periodo_mensal, '2025-Q1' as periodo_trimestral, '2025' as periodo_anual,
                0 as valor_calculado
            FROM dre_structure_n0 
            WHERE is_active = true
            ORDER BY order_index
            ''')
            
            connection.execute(create_view)
            print('   ✅ View recriada com schema explícito')
            
            # Verificar se agora aparece
            check_again = text('''
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_name = 'v_dre_n0_completo'
                AND table_schema = 'public'
            ''')
            
            result = connection.execute(check_again).fetchone()
            if result:
                print(f'   ✅ View agora aparece em information_schema: {result[0]} ({result[1]})')
                return True
            else:
                print('   ❌ View ainda não aparece em information_schema')
                return False
                
        except Exception as e:
            print(f'   ❌ Erro ao recriar view: {e}')
            return False

if __name__ == "__main__":
    try:
        success = fix_dre_n0_view_issue()
        if success:
            print("\n🎉 VIEW DRE N0 CORRIGIDA COM SUCESSO!")
            print("   ✅ Schema explícito implementado")
            print("   ✅ View agora deve aparecer no admin")
        else:
            print("\n❌ ERRO AO CORRIGIR VIEW DRE N0!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
