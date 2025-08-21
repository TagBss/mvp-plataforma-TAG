#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_correct_dre_n0_view():
    """Cria uma view correta usando UUIDs para fazer os JOINs"""
    
    engine = get_engine()
    
    with engine.connect() as connection:
        print("🔍 CRIANDO VIEW CORRETA DE DRE N0...")
        
        # 1. Remover a view antiga
        print("\n🗑️ REMOVENDO VIEW ANTIGA:")
        drop_view = text("""
            DROP VIEW IF EXISTS v_dre_n0_completo CASCADE
        """)
        
        try:
            connection.execute(drop_view)
            print("   ✅ View antiga removida com sucesso")
        except Exception as e:
            print(f"   ⚠️ Erro ao remover view: {e}")
        
        # 2. Criar a view correta usando UUIDs
        print("\n🔄 CRIANDO VIEW CORRETA:")
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
                    ELSE 0
                END as valor_calculado
            FROM dre_structure_n0 ds0
            LEFT JOIN financial_data fd ON (
                -- CORREÇÃO: Usar UUIDs corretos para o JOIN
                fd.dre_n1_id = ds0.dre_n1_id OR fd.dre_n2_id = ds0.dre_n2_id
            )
            WHERE ds0.is_active = true
            AND fd.valor_original IS NOT NULL
            AND fd.competencia IS NOT NULL
            GROUP BY ds0.id, ds0.name, ds0.operation_type, ds0.order_index, ds0.dre_niveis, ds0.description, 
                     TO_CHAR(fd.competencia, 'YYYY-MM'), 
                     CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)),
                     EXTRACT(YEAR FROM fd.competencia)::text
            ORDER BY ds0.order_index, TO_CHAR(fd.competencia, 'YYYY-MM')
        """)
        
        try:
            connection.execute(create_view)
            print("   ✅ View correta criada com sucesso")
        except Exception as e:
            print(f"   ❌ Erro ao criar view: {e}")
            return
        
        # 3. Verificar se a view foi criada
        print("\n✅ VERIFICANDO VIEW CRIADA:")
        check_view = text("""
            SELECT viewname
            FROM pg_views 
            WHERE viewname = 'v_dre_n0_completo'
            AND schemaname = 'public'
        """)
        
        result_view = connection.execute(check_view)
        view_created = result_view.fetchone()
        
        if view_created:
            print("   ✅ View v_dre_n0_completo criada e funcionando!")
        else:
            print("   ❌ View não foi criada")
            return
        
        # 4. Testar a nova view
        print("\n🔍 TESTANDO NOVA VIEW:")
        test_view = text("""
            SELECT COUNT(*) as total_registros
            FROM v_dre_n0_completo
        """)
        
        result_test = connection.execute(test_view)
        test_data = result_test.fetchone()
        
        if test_data:
            print(f"   ✅ View funcionando: {test_data.total_registros} registros encontrados")
        else:
            print("   ❌ View não retorna dados")
        
        # 5. Verificar alguns dados da view
        print("\n📊 DADOS DA VIEW:")
        check_data = text("""
            SELECT 
                name,
                operation_type,
                periodo_mensal,
                valor_calculado
            FROM v_dre_n0_completo
            WHERE valor_calculado IS NOT NULL
            ORDER BY order_index, periodo_mensal
            LIMIT 10
        """)
        
        result_data = connection.execute(check_data)
        dados_view = result_data.fetchall()
        print(f"   Dados encontrados: {len(dados_view)}")
        for row in dados_view:
            print(f"      - {row.name} ({row.operation_type}): {row.periodo_mensal} = {row.valor_calculado}")

if __name__ == "__main__":
    create_correct_dre_n0_view()
