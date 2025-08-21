#!/usr/bin/env python3
"""
Script para verificar views existentes e recriar views DRE N0 com novo fluxo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def check_and_recreate_dre_views():
    """Verifica views existentes e recria views DRE N0 com novo fluxo"""
    
    print("🔍 VERIFICANDO E RECRIANDO VIEWS DRE N0...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar quais views existem atualmente
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
            
            # 2. Verificar se views DRE N0 existem
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            missing_views = []
            
            for view_name in dre_views:
                exists = any(view[0] == view_name for view in existing_views)
                if exists:
                    print(f"   ✅ {view_name}: EXISTE")
                else:
                    print(f"   ❌ {view_name}: NÃO EXISTE")
                    missing_views.append(view_name)
            
            # 3. Verificar estrutura das tabelas para novo fluxo
            print("\n🔧 2. VERIFICANDO ESTRUTURA PARA NOVO FLUXO:")
            
            # Verificar se financial_data tem as colunas de relacionamento por UUID
            fd_columns_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'financial_data' 
                AND column_name IN ('dre_n1_id', 'dre_n2_id', 'dfc_n1_id', 'dfc_n2_id')
                ORDER BY column_name
            """)
            
            result = connection.execute(fd_columns_query)
            fd_columns = result.fetchall()
            
            print("   📋 Colunas de relacionamento em financial_data:")
            for col in fd_columns:
                print(f"      - {col[0]}: {col[1]}")
            
            # Verificar se dre_structure_n0 existe
            dre_structure_query = text("""
                SELECT COUNT(*) as total 
                FROM information_schema.tables 
                WHERE table_name = 'dre_structure_n0' 
                AND table_schema = 'public'
            """)
            
            result = connection.execute(dre_structure_query)
            dre_structure_exists = result.scalar() > 0
            
            print(f"   📊 dre_structure_n0: {'EXISTE' if dre_structure_exists else 'NÃO EXISTE'}")
            
            # 4. Recriar views DRE N0 com novo fluxo
            if missing_views and dre_structure_exists and len(fd_columns) >= 4:
                print("\n🔄 3. RECRIANDO VIEWS DRE N0 COM NOVO FLUXO:")
                
                # Drop views existentes se houver
                for view_name in dre_views:
                    try:
                        drop_query = text(f"DROP VIEW IF EXISTS {view_name} CASCADE")
                        connection.execute(drop_query)
                        print(f"   🗑️ {view_name}: Drop executado")
                    except Exception as e:
                        print(f"   ⚠️ {view_name}: Erro no drop - {e}")
                
                # Criar v_dre_n0_completo com novo fluxo
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
                    COALESCE(
                        (SELECT json_build_object(
                            'total', COALESCE(SUM(fd.valor_original), 0),
                            'count', COUNT(*)
                        ) FROM financial_data fd 
                         WHERE fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL), 
                        '{}'::jsonb
                    ) as valores_mensais,
                    COALESCE(
                        (SELECT json_build_object(
                            'total', COALESCE(SUM(fd.valor_original), 0),
                            'count', COUNT(*)
                        ) FROM financial_data fd 
                         WHERE fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL), 
                        '{}'::jsonb
                    ) as valores_trimestrais,
                    COALESCE(
                        (SELECT json_build_object(
                            'total', COALESCE(SUM(fd.valor_original), 0),
                            'count', COUNT(*)
                        ) FROM financial_data fd 
                         WHERE fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL), 
                        '{}'::jsonb
                    ) as valores_anuais,
                    '{}'::jsonb as orcamentos_mensais,
                    '{}'::jsonb as orcamentos_trimestrais,
                    '{}'::jsonb as orcamentos_anuais,
                    0 as orcamento_total,
                    COALESCE(
                        (SELECT COALESCE(SUM(fd.valor_original), 0) 
                         FROM financial_data fd 
                         WHERE fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL), 
                        0
                    ) as valor_total,
                    'dre_structure_n0' as source
                FROM dre_structure_n0 ds0
                WHERE ds0.is_active = true
                ORDER BY ds0.order_index
                """)
                
                try:
                    connection.execute(create_completo_query)
                    print("   ✅ v_dre_n0_completo: Criada com sucesso")
                except Exception as e:
                    print(f"   ❌ v_dre_n0_completo: Erro na criação - {e}")
                
                # Criar v_dre_n0_simples
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
                    print(f"   ❌ v_dre_n0_simples: Erro na criação - {e}")
                
                # Criar v_dre_n0_por_periodo
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
                    print(f"   ❌ v_dre_n0_por_periodo: Erro na criação - {e}")
                
                # 5. Verificar se as views foram criadas
                print("\n🔍 4. VERIFICANDO VIEWS RECRIADAS:")
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
                        except Exception as e:
                            print(f"      ❌ Erro ao testar: {e}")
                    else:
                        print(f"   ❌ {view_name}: NÃO FOI CRIADA")
                
            else:
                print("\n⚠️ 3. NÃO É POSSÍVEL RECRIAR VIEWS:")
                if not dre_structure_exists:
                    print("   ❌ dre_structure_n0 não existe")
                if len(fd_columns) < 4:
                    print(f"   ❌ Colunas de relacionamento insuficientes: {len(fd_columns)}/4")
                if not missing_views:
                    print("   ✅ Todas as views DRE N0 já existem")
            
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = check_and_recreate_dre_views()
        if success:
            print("\n🎯 PROCESSO CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO PROCESSO!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
