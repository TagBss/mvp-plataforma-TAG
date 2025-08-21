#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_simple_dre_n0_view():
    """Cria uma view simples de DRE N0 que funcione com os dados atuais"""
    
    engine = get_engine()
    
    with engine.connect() as connection:
        print("🔍 CRIANDO VIEW SIMPLES DE DRE N0...")
        
        # 1. Verificar se a view antiga existe
        print("\n📊 VERIFICANDO VIEW EXISTENTE:")
        check_view = text("""
            SELECT viewname, definition
            FROM pg_views 
            WHERE viewname = 'v_dre_n0_completo'
            AND schemaname = 'public'
        """)
        
        result_view = connection.execute(check_view)
        view_exists = result_view.fetchone()
        
        if view_exists:
            print("   ✅ View v_dre_n0_completo existe")
        else:
            print("   ❌ View não existe")
        
        # 2. Remover a view antiga
        print("\n🗑️ REMOVENDO VIEW ANTIGA:")
        drop_view = text("""
            DROP VIEW IF EXISTS v_dre_n0_completo CASCADE
        """)
        
        try:
            connection.execute(drop_view)
            print("   ✅ View antiga removida com sucesso")
        except Exception as e:
            print(f"   ⚠️ Erro ao remover view: {e}")
        
        # 3. Criar uma view simples que funcione
        print("\n🔄 CRIANDO VIEW SIMPLES:")
        create_view = text("""
            CREATE VIEW v_dre_n0_completo AS
            SELECT 
                ds0.id,
                ds0.name,
                ds0.operation_type,
                ds0.order_index,
                ds0.dre_niveis,
                ds0.description,
                -- Dados financeiros agregados por período
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                -- Valores calculados
                CASE 
                    WHEN ds0.operation_type = '+' THEN ABS(SUM(fd.valor_original))
                    WHEN ds0.operation_type = '-' THEN -ABS(SUM(fd.valor_original))
                    WHEN ds0.operation_type = '+/-' THEN SUM(fd.valor_original)
                END as valor_calculado
            FROM dre_structure_n0 ds0
            LEFT JOIN financial_data fd ON (
                -- Usar apenas relacionamentos por ID
                (fd.dre_n1_id = ds0.id) OR (fd.dre_n2_id = ds0.id)
            )
            WHERE ds0.is_active = true
            GROUP BY ds0.id, ds0.name, ds0.operation_type, ds0.order_index, ds0.dre_niveis, ds0.description
            ORDER BY ds0.order_index, ds0.name
        """)
        
        try:
            connection.execute(create_view)
            print("   ✅ View simples criada com sucesso")
        except Exception as e:
            print(f"   ❌ Erro ao criar view: {e}")
            return
        
        # 4. Verificar se a view foi criada
        print("\n✅ VERIFICANDO VIEW CRIADA:")
        check_new_view = text("""
            SELECT viewname, definition
            FROM pg_views 
            WHERE viewname = 'v_dre_n0_completo'
            AND schemaname = 'public'
        """)
        
        result_new_view = connection.execute(check_new_view)
        view_created = result_new_view.fetchone()
        
        if view_created:
            print("   ✅ View v_dre_n0_completo criada e funcionando!")
        else:
            print("   ❌ View não foi criada")
            return
        
        # 5. Testar a nova view
        print("\n🔍 TESTANDO NOVA VIEW:")
        test_view = text("""
            SELECT COUNT(*) as total_registros
            FROM v_dre_n0_completo
            LIMIT 1
        """)
        
        result_test = connection.execute(test_view)
        test_data = result_test.fetchone()
        
        if test_data:
            print(f"   ✅ View funcionando: {test_data.total_registros} registros encontrados")
        else:
            print("   ❌ View não retorna dados")
        
        # 6. Verificar estrutura final
        print("\n📊 ESTRUTURA FINAL:")
        check_final = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'v_dre_n0_completo'
            ORDER BY column_name
        """)
        
        result_final = connection.execute(check_final)
        colunas_finais = result_final.fetchall()
        print(f"   Colunas da view: {len(colunas_finais)}")
        for col in colunas_finais:
            print(f"      - {col.column_name} ({col.data_type})")

if __name__ == "__main__":
    create_simple_dre_n0_view()
