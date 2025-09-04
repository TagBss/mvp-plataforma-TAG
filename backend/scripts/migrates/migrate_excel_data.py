"""
Script para migrar dados do Excel para PostgreSQL usando Drizzle ORM
"""
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any
from database.connection import get_database
from database.schema import financial_data, categories
from database.repository import FinancialDataRepository

def migrate_excel_to_postgres(excel_file: str = "db_bluefit - Copia.xlsx"):
    """Migra dados do Excel para PostgreSQL"""
    
    print(f"📊 Iniciando migração do arquivo: {excel_file}")
    
    try:
        # Carregar dados do Excel
        print("📂 Carregando dados do Excel...")
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        print(f"📈 Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Processar e inserir dados
        db = get_database()
        repository = FinancialDataRepository()
        
        # Mapear colunas do Excel para o schema
        column_mapping = {
            'Data': 'date',
            'Categoria': 'category',
            'Descrição': 'description',
            'Valor': 'value',
            'Tipo': 'type',
            'Período': 'period',
            'Fonte': 'source',
            'Orçado': 'is_budget'
        }
        
        # Renomear colunas se necessário
        df = df.rename(columns=column_mapping)
        
        # Processar cada linha
        inserted_count = 0
        error_count = 0
        
        with db.connect() as conn:
            for index, row in df.iterrows():
                try:
                    # Preparar dados para inserção
                    data = {
                        'category': str(row.get('category', '')),
                        'description': str(row.get('description', '')),
                        'value': Decimal(str(row.get('value', 0))),
                        'type': str(row.get('type', 'despesa')),
                        'date': pd.to_datetime(row.get('date')).date(),
                        'period': str(row.get('period', 'mensal')),
                        'source': str(row.get('source', 'excel_migration')),
                        'is_budget': bool(row.get('is_budget', False)),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Inserir no banco
                    conn.execute(
                        financial_data.insert().values(**data)
                    )
                    
                    inserted_count += 1
                    
                    if inserted_count % 100 == 0:
                        print(f"✅ Inseridas {inserted_count} linhas...")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ Erro na linha {index}: {e}")
                    continue
        
        print(f"✅ Migração concluída!")
        print(f"📊 Total inserido: {inserted_count} registros")
        print(f"❌ Erros: {error_count} registros")
        
        # Criar categorias baseadas nos dados
        create_categories_from_data(df)
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        raise

def create_categories_from_data(df: pd.DataFrame):
    """Cria categorias baseadas nos dados do Excel"""
    
    print("📂 Criando categorias baseadas nos dados...")
    
    # Extrair categorias únicas
    unique_categories = df['category'].dropna().unique()
    
    db = get_database()
    
    with db.connect() as conn:
        for category_name in unique_categories:
            if category_name and str(category_name).strip():
                try:
                    # Verificar se categoria já existe
                    existing = conn.execute(
                        categories.select().where(categories.name == str(category_name))
                    ).fetchone()
                    
                    if not existing:
                        # Inserir nova categoria
                        conn.execute(
                            categories.insert().values(
                                name=str(category_name),
                                code=str(category_name).lower().replace(' ', '_'),
                                level=1,
                                is_active=True,
                                created_at=datetime.now()
                            )
                        )
                        print(f"✅ Categoria criada: {category_name}")
                
                except Exception as e:
                    print(f"❌ Erro ao criar categoria {category_name}: {e}")

def validate_migration():
    """Valida a migração comparando dados"""
    
    print("🔍 Validando migração...")
    
    # Carregar dados do Excel
    df_excel = pd.read_excel("db_bluefit - Copia.xlsx", engine='openpyxl')
    
    # Buscar dados do PostgreSQL
    repository = FinancialDataRepository()
    db_data = repository.get_financial_data()
    
    print(f"📊 Excel: {len(df_excel)} registros")
    print(f"📊 PostgreSQL: {len(db_data)} registros")
    
    # Comparar totais
    excel_total = df_excel['Valor'].sum()
    postgres_total = sum(Decimal(str(row['value'])) for row in db_data)
    
    print(f"💰 Total Excel: R$ {excel_total:,.2f}")
    print(f"💰 Total PostgreSQL: R$ {postgres_total:,.2f}")
    
    difference = abs(excel_total - float(postgres_total))
    print(f"📈 Diferença: R$ {difference:,.2f}")
    
    if difference < 0.01:  # Tolerância de 1 centavo
        print("✅ Migração validada com sucesso!")
    else:
        print("⚠️ Diferenças encontradas na migração")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            migrate_excel_to_postgres()
        elif command == "validate":
            validate_migration()
        else:
            print("Comandos: migrate, validate")
    else:
        print("Comandos: migrate, validate")
