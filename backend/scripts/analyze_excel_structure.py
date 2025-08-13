#!/usr/bin/env python3
"""
Script para analisar a estrutura do Excel e comparar com PostgreSQL
"""
import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text

def analyze_excel_structure():
    """Analisa a estrutura do Excel"""
    print("=== ANÁLISE DO EXCEL ===")
    
    # Ler Excel
    excel_file = 'db_bluefit - Copia.xlsx'
    df = pd.read_excel(excel_file)
    
    print(f"Total de registros: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}")
    
    print("\nColunas encontradas:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # Verificar colunas de data
    print("\nColunas relacionadas a data:")
    date_related = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['data', 'emiss', 'venc', 'compet']):
            date_related.append(col)
    
    for col in date_related:
        print(f"  - {col}")
        # Mostrar alguns valores de exemplo
        sample_values = df[col].dropna().head(3).tolist()
        print(f"    Exemplos: {sample_values}")
    
    return df

def analyze_postgres_structure():
    """Analisa a estrutura do PostgreSQL"""
    print("\n=== ANÁLISE DO POSTGRESQL ===")
    
    with DatabaseSession() as session:
        # Verificar estrutura da tabela
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financial_data' 
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        
        print("Estrutura da tabela financial_data:")
        for col_name, data_type, is_nullable, default in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  {col_name}: {data_type} {nullable}{default_str}")
        
        # Verificar dados de amostra
        result = session.execute(text("SELECT * FROM financial_data LIMIT 3"))
        sample_data = result.fetchall()
        
        if sample_data:
            print(f"\nAmostra de dados (primeiras 3 linhas):")
            columns_names = [desc[0] for desc in result.description]
            
            for i, row in enumerate(sample_data, 1):
                print(f"\nLinha {i}:")
                for col_name, value in zip(columns_names, row):
                    print(f"  {col_name}: {value}")

def compare_and_recommend():
    """Compara estruturas e faz recomendações"""
    print("\n=== COMPARAÇÃO E RECOMENDAÇÕES ===")
    
    # Ler Excel
    df = pd.read_excel('db_bluefit - Copia.xlsx')
    excel_columns = set(df.columns)
    
    # Obter colunas do PostgreSQL
    with DatabaseSession() as session:
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financial_data'
        """))
        postgres_columns = set(row[0] for row in result.fetchall())
    
    print("Mapeamento recomendado:")
    print("Excel -> PostgreSQL")
    print("-" * 40)
    
    # Mapeamento baseado na análise
    mapping = {
        'dfc_n1': 'category (renomear para dfc_n1)',
        'dfc_n2': 'subcategory (renomear para dfc_n2)', 
        'origem': 'source (já existe)',
        'observação': 'description (já existe)',
        'valor': 'value (já existe)',
        'data': 'date (já existe)',
        'competencia': 'competencia (ADICIONAR)',
        'emissao': 'emissao (ADICIONAR)',
        'vencimento': 'vencimento (ADICIONAR)'
    }
    
    for excel_col, postgres_action in mapping.items():
        if excel_col in excel_columns:
            print(f"✅ {excel_col} -> {postgres_action}")
        else:
            print(f"❌ {excel_col} -> {postgres_action} (coluna não encontrada no Excel)")
    
    print("\nColunas do Excel não mapeadas:")
    mapped_excel_cols = set(mapping.keys())
    unmapped = excel_columns - mapped_excel_cols
    for col in sorted(unmapped):
        print(f"  ? {col}")

if __name__ == "__main__":
    try:
        df = analyze_excel_structure()
        analyze_postgres_structure()
        compare_and_recommend()
    except Exception as e:
        print(f"Erro: {e}")
