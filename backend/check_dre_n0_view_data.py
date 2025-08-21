#!/usr/bin/env python3
"""
Script para verificar os dados retornados pela view dre_n0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def check_dre_n0_view_data():
    """Verifica os dados retornados pela view dre_n0"""
    
    print("🔍 VERIFICANDO DADOS DA VIEW DRE N0...")
    
    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            
            # 1. Verificar se a view existe
            print("\n📋 1. VERIFICANDO EXISTÊNCIA DA VIEW:")
            check_view_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_name = 'v_dre_n0_completo' 
                AND table_schema = 'public'
            """)
            
            result = connection.execute(check_view_query)
            view_exists = result.fetchone()
            
            if view_exists:
                print(f"   ✅ View encontrada: {view_exists[0]} ({view_exists[1]})")
            else:
                print("   ❌ View v_dre_n0_completo não encontrada!")
                return False
            
            # 2. Verificar estrutura da view
            print("\n📊 2. VERIFICANDO ESTRUTURA DA VIEW:")
            structure_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'v_dre_n0_completo' 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            result = connection.execute(structure_query)
            columns = result.fetchall()
            
            print("   📋 Colunas da view:")
            for col in columns:
                print(f"      - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # 3. Verificar dados retornados
            print("\n📈 3. VERIFICANDO DADOS RETORNADOS:")
            data_query = text("SELECT * FROM v_dre_n0_completo LIMIT 5")
            
            result = connection.execute(data_query)
            rows = result.fetchall()
            
            if rows:
                print(f"   📊 Primeiros 5 registros:")
                for i, row in enumerate(rows, 1):
                    print(f"      {i}. {dict(row)}")
            else:
                print("   ❌ View não retorna dados!")
            
            # 4. Verificar total de registros
            print("\n🔢 4. VERIFICANDO TOTAL DE REGISTROS:")
            count_query = text("SELECT COUNT(*) as total FROM v_dre_n0_completo")
            
            result = connection.execute(count_query)
            total = result.scalar()
            
            print(f"   📊 Total de registros: {total}")
            
            # 5. Verificar valores específicos
            print("\n💰 5. VERIFICANDO VALORES ESPECÍFICOS:")
            
            # Verificar se há valores não vazios
            values_query = text("""
                SELECT 
                    nome_conta,
                    valores_mensais,
                    valores_trimestrais,
                    valores_anuais,
                    valor_total
                FROM v_dre_n0_completo 
                WHERE valores_mensais != '{}' 
                OR valores_trimestrais != '{}' 
                OR valores_anuais != '{}'
                OR valor_total != 0
                LIMIT 3
            """)
            
            result = connection.execute(values_query)
            rows_with_values = result.fetchall()
            
            if rows_with_values:
                print("   💰 Registros com valores:")
                for row in rows_with_values:
                    print(f"      - {row[0]}:")
                    print(f"        Mensais: {row[1]}")
                    print(f"        Trimestrais: {row[2]}")
                    print(f"        Anuais: {row[3]}")
                    print(f"        Total: {row[4]}")
            else:
                print("   ⚠️ Todos os registros têm valores vazios ou zerados")
            
            # 6. Verificar dados de exemplo
            print("\n🔍 6. VERIFICANDO DADOS DE EXEMPLO:")
            sample_query = text("""
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    origem,
                    empresa,
                    source
                FROM v_dre_n0_completo 
                ORDER BY ordem 
                LIMIT 5
            """)
            
            result = connection.execute(sample_query)
            sample_rows = result.fetchall()
            
            print("   📋 Dados de exemplo:")
            for row in sample_rows:
                print(f"      - {row[1]} (ID: {row[0]}, Tipo: {row[2]}, Ordem: {row[3]})")
                print(f"        Descrição: {row[4]}")
                print(f"        Origem: {row[5]}, Empresa: {row[6]}, Source: {row[7]}")
            
            return True
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = check_dre_n0_view_data()
        if success:
            print("\n🎯 VERIFICAÇÃO CONCLUÍDA!")
        else:
            print("\n❌ ERRO NA VERIFICAÇÃO!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
