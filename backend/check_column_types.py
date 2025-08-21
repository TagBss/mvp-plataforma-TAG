#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def check_column_types():
    """Verifica os tipos exatos das colunas das tabelas"""
    
    engine = get_engine()
    
    with engine.connect() as connection:
        print("🔍 VERIFICANDO TIPOS DAS COLUNAS...")
        
        # 1. Verificar tipos da tabela financial_data
        print("\n📊 TIPOS DA TABELA FINANCIAL_DATA:")
        check_financial = text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'financial_data'
            AND (column_name LIKE '%dre%' OR column_name LIKE '%dfc%')
            ORDER BY column_name
        """)
        
        result_financial = connection.execute(check_financial)
        colunas_financial = result_financial.fetchall()
        print(f"   Colunas DRE/DFC encontradas: {len(colunas_financial)}")
        for col in colunas_financial:
            print(f"      - {col.column_name}: {col.data_type} (max: {col.character_maximum_length}) - Nullable: {col.is_nullable}")
        
        # 2. Verificar tipos da tabela dre_structure_n0
        print("\n📊 TIPOS DA TABELA DRE_STRUCTURE_N0:")
        check_dre_n0 = text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'dre_structure_n0'
            ORDER BY column_name
        """)
        
        result_dre_n0 = connection.execute(check_dre_n0)
        colunas_dre_n0 = result_dre_n0.fetchall()
        print(f"   Colunas encontradas: {len(colunas_dre_n0)}")
        for col in colunas_dre_n0:
            print(f"      - {col.column_name}: {col.data_type} (max: {col.character_maximum_length}) - Nullable: {col.is_nullable}")
        
        # 3. Verificar tipos da tabela dre_structure_n1
        print("\n📊 TIPOS DA TABELA DRE_STRUCTURE_N1:")
        check_dre_n1 = text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'dre_structure_n1'
            ORDER BY column_name
        """)
        
        result_dre_n1 = connection.execute(check_dre_n1)
        colunas_dre_n1 = result_dre_n1.fetchall()
        print(f"   Colunas encontradas: {len(colunas_dre_n1)}")
        for col in colunas_dre_n1:
            print(f"      - {col.column_name}: {col.data_type} (max: {col.character_maximum_length}) - Nullable: {col.is_nullable}")
        
        # 4. Verificar tipos da tabela dre_structure_n2
        print("\n📊 TIPOS DA TABELA DRE_STRUCTURE_N2:")
        check_dre_n2 = text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'dre_structure_n2'
            ORDER BY column_name
        """)
        
        result_dre_n2 = connection.execute(check_dre_n2)
        colunas_dre_n2 = result_dre_n2.fetchall()
        print(f"   Colunas encontradas: {len(colunas_dre_n2)}")
        for col in colunas_dre_n2:
            print(f"      - {col.column_name}: {col.data_type} (max: {col.character_maximum_length}) - Nullable: {col.is_nullable}")
        
        # 5. Verificar alguns dados de exemplo
        print("\n🔍 DADOS DE EXEMPLO:")
        check_example = text("""
            SELECT 
                'dre_structure_n0' as tabela,
                id,
                name,
                dre_niveis
            FROM dre_structure_n0 
            LIMIT 3
            
            UNION ALL
            
            SELECT 
                'dre_structure_n1' as tabela,
                id,
                name,
                dre_niveis
            FROM dre_structure_n1 
            LIMIT 3
            
            UNION ALL
            
            SELECT 
                'dre_structure_n2' as tabela,
                id,
                name,
                dre_niveis
            FROM dre_structure_n2 
            LIMIT 3
        """)
        
        result_example = connection.execute(check_example)
        dados_exemplo = result_example.fetchall()
        print(f"   Dados de exemplo:")
        for row in dados_exemplo:
            print(f"      - {row.tabela}: ID={row.id} ({type(row.id).__name__}), Nome={row.name}, Níveis={row.dre_niveis}")

if __name__ == "__main__":
    check_column_types()
