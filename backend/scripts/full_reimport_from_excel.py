#!/usr/bin/env python3
"""
Script para reimportar completamente os dados do Excel
Irá excluir todos os registros e recriar a tabela com as colunas exatas do Excel
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys
from datetime import datetime

def analyze_excel_structure():
    """Analisar estrutura do Excel"""
    print("🔍 Analisando estrutura do Excel...")
    
    try:
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        print(f"📊 Excel carregado: {len(df)} registros, {len(df.columns)} colunas")
        
        print("\n📋 Colunas no Excel:")
        for i, col in enumerate(df.columns, 1):
            sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            print(f"{i:2d}. {col:<25} | Tipo: {str(df[col].dtype):<15} | Exemplo: {sample_value}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return None

def map_pandas_to_postgresql_type(pandas_dtype, column_name):
    """Mapear tipos do pandas para PostgreSQL"""
    dtype_str = str(pandas_dtype)
    
    if 'datetime' in dtype_str or 'timestamp' in dtype_str:
        return 'TIMESTAMP'
    elif 'int' in dtype_str:
        return 'INTEGER'
    elif 'float' in dtype_str:
        return 'DECIMAL(15,2)'
    elif 'bool' in dtype_str:
        return 'BOOLEAN'
    else:
        # Para strings, definir tamanho baseado no conteúdo
        if column_name in ['description', 'observação']:
            return 'TEXT'
        else:
            return 'VARCHAR(255)'

def recreate_table_structure(df):
    """Recriar estrutura da tabela baseada no Excel"""
    print("\n🔧 Recriando estrutura da tabela...")
    
    try:
        with DatabaseSession() as session:
            # 1. Fazer backup dos dados existentes (opcional)
            print("  📋 Fazendo backup da estrutura atual...")
            
            # 2. Excluir todos os registros
            print("  🗑️  Excluindo todos os registros...")
            session.execute(text("DELETE FROM financial_data"))
            session.commit()
            print("    ✅ Registros excluídos")
            
            # 3. Verificar colunas existentes
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financial_data'
                ORDER BY ordinal_position
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"    📋 Colunas existentes: {len(existing_columns)}")
            
            # 4. Adicionar colunas que não existem
            excel_columns = df.columns.tolist()
            
            for col in excel_columns:
                # Normalizar nome da coluna (remover espaços, caracteres especiais)
                normalized_col = col.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c').replace('é', 'e')
                
                if normalized_col not in existing_columns:
                    pg_type = map_pandas_to_postgresql_type(df[col].dtype, col)
                    print(f"    ➕ Adicionando coluna: {normalized_col} ({pg_type})")
                    
                    try:
                        session.execute(text(f"ALTER TABLE financial_data ADD COLUMN {normalized_col} {pg_type}"))
                    except Exception as e:
                        print(f"      ⚠️  Erro ao adicionar {normalized_col}: {e}")
            
            # 5. Verificar se precisamos da coluna ID
            if 'id' not in existing_columns:
                print("    ➕ Adicionando coluna ID...")
                session.execute(text("ALTER TABLE financial_data ADD COLUMN id SERIAL PRIMARY KEY"))
            
            session.commit()
            print("  ✅ Estrutura da tabela atualizada")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao recriar estrutura: {e}")
        return False

def import_excel_data(df):
    """Importar dados do Excel para a tabela"""
    print("\n📥 Importando dados do Excel...")
    
    try:
        with DatabaseSession() as session:
            # Mapear nomes das colunas
            column_mapping = {}
            for col in df.columns:
                normalized = col.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c').replace('é', 'e')
                column_mapping[col] = normalized
            
            print(f"  📋 Mapeamento de colunas:")
            for orig, norm in column_mapping.items():
                print(f"    {orig} → {norm}")
            
            # Preparar dados para inserção
            print(f"  📊 Preparando {len(df)} registros para inserção...")
            
            inserted_count = 0
            batch_size = 1000
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                print(f"    📦 Processando lote {i//batch_size + 1}: registros {i+1} a {min(i+batch_size, len(df))}")
                
                for _, row in batch.iterrows():
                    # Preparar valores para inserção
                    values = {}
                    columns = []
                    placeholders = []
                    
                    for excel_col, db_col in column_mapping.items():
                        value = row[excel_col]
                        
                        # Tratar valores NaN/None
                        if pd.isna(value):
                            value = None
                        elif isinstance(value, pd.Timestamp):
                            # Converter timestamps para string ISO
                            value = value.isoformat()
                        
                        values[db_col] = value
                        columns.append(db_col)
                        placeholders.append(f":{db_col}")
                    
                    # Montar SQL de inserção
                    insert_sql = f"""
                        INSERT INTO financial_data ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    try:
                        session.execute(text(insert_sql), values)
                        inserted_count += 1
                    except Exception as e:
                        print(f"      ⚠️  Erro ao inserir registro {inserted_count + 1}: {e}")
                        # Mostrar valores problemáticos
                        print(f"         Valores: {values}")
                        continue
                
                # Commit do lote
                session.commit()
                print(f"    ✅ Lote commitado: {inserted_count} registros inseridos até agora")
            
            print(f"  ✅ Importação concluída: {inserted_count} registros inseridos")
            return inserted_count
            
    except Exception as e:
        print(f"❌ Erro durante importação: {e}")
        return 0

def verify_import():
    """Verificar se a importação foi bem-sucedida"""
    print("\n🔍 Verificando importação...")
    
    try:
        with DatabaseSession() as session:
            # Contar registros
            result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
            total_count = result.fetchone()[0]
            print(f"  📊 Total de registros na tabela: {total_count}")
            
            # Verificar estrutura
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financial_data'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"  📋 Total de colunas: {len(columns)}")
            
            # Mostrar algumas amostras
            result = session.execute(text("SELECT * FROM financial_data LIMIT 3"))
            samples = result.fetchall()
            
            print(f"\n  📋 Amostra dos dados (primeiros 3 registros):")
            for i, sample in enumerate(samples, 1):
                print(f"    Registro {i}:")
                for j, value in enumerate(sample):
                    if j < len(columns):
                        col_name = columns[j]
                        display_value = str(value)[:50] + "..." if value and len(str(value)) > 50 else value
                        print(f"      {col_name}: {display_value}")
                print()
            
            return total_count
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal"""
    print("🚀 REIMPORTAÇÃO COMPLETA DOS DADOS DO EXCEL")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    try:
        # 1. Analisar Excel
        df = analyze_excel_structure()
        if df is None:
            sys.exit(1)
        
        # 2. Recriar estrutura da tabela
        if not recreate_table_structure(df):
            sys.exit(1)
        
        # 3. Importar dados
        imported_count = import_excel_data(df)
        if imported_count == 0:
            print("❌ Nenhum registro foi importado!")
            sys.exit(1)
        
        # 4. Verificar resultado
        final_count = verify_import()
        
        print("\n" + "=" * 60)
        print("🎉 REIMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Registros importados: {imported_count}")
        print(f"📋 Registros na tabela: {final_count}")
        print(f"📈 Colunas do Excel: {len(df.columns)}")
        print(f"✅ Status: {'SUCESSO' if imported_count == final_count else 'VERIFICAR DIFERENÇAS'}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
