"""
Script para migrar dados do Excel para PostgreSQL usando SQLAlchemy
"""
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData, Category
from database.repository_sqlalchemy import FinancialDataRepository

def migrate_excel_to_postgres(excel_file: str = "db_bluefit - Copia.xlsx"):
    """Migra dados do Excel para PostgreSQL"""
    
    print(f"📊 Iniciando migração do arquivo: {excel_file}")
    
    try:
        # Carregar dados do Excel - sheet 'base'
        print("📂 Carregando dados do Excel (sheet 'base')...")
        df = pd.read_excel(excel_file, sheet_name='base')
        
        print(f"📈 Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Processar e inserir dados
        repository = FinancialDataRepository()
        
        # Mapear colunas do Excel para o schema
        column_mapping = {
            'dre_n1': 'category',
            'dre_n2': 'subcategory',
            'observação': 'description',
            'valor': 'value',
            'data': 'date',
            'competencia': 'period',
            'origem': 'source',
            'empresa': 'company'
        }
        
        # Renomear colunas se necessário
        df = df.rename(columns=column_mapping)
        
        # Processar cada linha
        inserted_count = 0
        error_count = 0
        
        with DatabaseSession() as session:
            for index, row in df.iterrows():
                try:
                    # Determinar tipo baseado na categoria
                    category = str(row.get('category', '')).lower()
                    if 'receita' in category or 'venda' in category:
                        data_type = 'receita'
                    elif 'despesa' in category or 'custo' in category:
                        data_type = 'despesa'
                    else:
                        data_type = 'outros'
                    
                    # Preparar dados para inserção
                    data = {
                        'category': str(row.get('category', '')),
                        'subcategory': str(row.get('subcategory', '')),
                        'description': str(row.get('description', '')),
                        'value': float(row.get('value', 0)),
                        'type': data_type,
                        'date': pd.to_datetime(row.get('date')).date() if pd.notna(row.get('date')) else date.today(),
                        'period': str(row.get('period', 'mensal')),
                        'source': str(row.get('source', 'bluefit_migration')),
                        'is_budget': False,  # Assumindo que são dados realizados
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Inserir no banco
                    financial_data = FinancialData(**data)
                    session.add(financial_data)
                    
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
    
    with DatabaseSession() as session:
        for category_name in unique_categories:
            if category_name and str(category_name).strip():
                try:
                    # Verificar se categoria já existe
                    existing = session.query(Category).filter(Category.name == str(category_name)).first()
                    
                    if not existing:
                        # Inserir nova categoria
                        category = Category(
                            name=str(category_name),
                            code=str(category_name).lower().replace(' ', '_').replace('(', '').replace(')', ''),
                            level=1,
                            is_active=True,
                            created_at=datetime.now()
                        )
                        session.add(category)
                        print(f"✅ Categoria criada: {category_name}")
                
                except Exception as e:
                    print(f"❌ Erro ao criar categoria {category_name}: {e}")

def validate_migration():
    """Valida a migração comparando dados"""
    
    print("🔍 Validando migração...")
    
    # Carregar dados do Excel
    df_excel = pd.read_excel("db_bluefit - Copia.xlsx", sheet_name='base')
    
    # Buscar dados do PostgreSQL
    repository = FinancialDataRepository()
    db_data = repository.get_financial_data()
    
    print(f"📊 Excel: {len(df_excel)} registros")
    print(f"📊 PostgreSQL: {len(db_data)} registros")
    
    # Comparar totais
    excel_total = df_excel['valor'].sum()
    postgres_total = sum(float(row['value']) for row in db_data)
    
    print(f"💰 Total Excel: R$ {excel_total:,.2f}")
    print(f"💰 Total PostgreSQL: R$ {postgres_total:,.2f}")
    
    difference = abs(excel_total - postgres_total)
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
