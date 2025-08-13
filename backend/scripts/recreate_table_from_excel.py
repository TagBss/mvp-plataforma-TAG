#!/usr/bin/env python3
"""
Script para recriar a tabela financial_data do ZERO
com APENAS as colunas que existem no Excel
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys
from datetime import datetime

def get_excel_columns():
    """Obter exatamente as colunas do Excel"""
    try:
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        
        print("📊 COLUNAS DO EXCEL:")
        print("=" * 50)
        
        column_info = []
        for i, col in enumerate(df.columns, 1):
            # Normalizar nome da coluna para PostgreSQL
            normalized = col.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c').replace('é', 'e')
            
            # Determinar tipo PostgreSQL
            dtype = df[col].dtype
            if 'datetime' in str(dtype) or 'timestamp' in str(dtype):
                pg_type = 'DATE'
            elif 'int' in str(dtype):
                pg_type = 'INTEGER'
            elif 'float' in str(dtype):
                pg_type = 'DECIMAL(15,2)'
            else:
                if col in ['description', 'observação']:
                    pg_type = 'TEXT'
                else:
                    pg_type = 'VARCHAR(255)'
            
            column_info.append({
                'original': col,
                'normalized': normalized,
                'pg_type': pg_type,
                'sample': df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            })
            
            print(f"{i:2d}. {col:<25} → {normalized:<25} | {pg_type:<15} | Ex: {str(column_info[-1]['sample'])[:30]}")
        
        print(f"\\nTotal: {len(column_info)} colunas")
        return df, column_info
        
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return None, None

def recreate_table_from_scratch(column_info):
    """Recriar tabela do zero"""
    print("\\n🔧 RECRIANDO TABELA DO ZERO...")
    print("=" * 40)
    
    try:
        with DatabaseSession() as session:
            # 1. Fazer backup se necessário
            print("1. 🗑️  Excluindo tabela atual...")
            session.execute(text("DROP TABLE IF EXISTS financial_data_backup"))
            session.execute(text("CREATE TABLE financial_data_backup AS SELECT * FROM financial_data"))
            print("   ✅ Backup criado: financial_data_backup")
            
            # 2. Excluir tabela atual
            session.execute(text("DROP TABLE IF EXISTS financial_data"))
            print("   ✅ Tabela financial_data excluída")
            
            # 3. Criar nova tabela
            print("2. 🏗️  Criando nova tabela...")
            
            create_sql = "CREATE TABLE financial_data (\\n"
            create_sql += "    id SERIAL PRIMARY KEY,\\n"
            
            for col_info in column_info:
                create_sql += f"    {col_info['normalized']} {col_info['pg_type']},\\n"
            
            create_sql = create_sql.rstrip(',\\n') + "\\n)"
            
            print("   SQL:")
            print("   " + create_sql.replace('\\n', '\\n   '))
            
            session.execute(text(create_sql))
            session.commit()
            print("   ✅ Nova tabela criada")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao recriar tabela: {e}")
        return False

def import_data(df, column_info):
    """Importar dados do Excel"""
    print("\\n📥 IMPORTANDO DADOS...")
    print("=" * 30)
    
    try:
        with DatabaseSession() as session:
            print(f"📊 Importando {len(df)} registros...")
            
            # Preparar mapeamento de colunas
            column_mapping = {col['original']: col['normalized'] for col in column_info}
            
            inserted_count = 0
            batch_size = 500
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                print(f"  📦 Lote {i//batch_size + 1}: registros {i+1}-{min(i+batch_size, len(df))}")
                
                for _, row in batch.iterrows():
                    # Preparar dados para inserção
                    columns = []
                    placeholders = []
                    values = {}
                    
                    for excel_col, db_col in column_mapping.items():
                        value = row[excel_col]
                        
                        # Tratar valores especiais
                        if pd.isna(value):
                            value = None
                        elif isinstance(value, pd.Timestamp):
                            value = value.date()  # Converter para data apenas
                        
                        columns.append(db_col)
                        placeholders.append(f":{db_col}")
                        values[db_col] = value
                    
                    # Inserir registro
                    insert_sql = f"""
                        INSERT INTO financial_data ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    try:
                        session.execute(text(insert_sql), values)
                        inserted_count += 1
                    except Exception as e:
                        print(f"    ⚠️  Erro no registro {inserted_count + 1}: {e}")
                        continue
                
                # Commit do lote
                session.commit()
                print(f"    ✅ {inserted_count} registros inseridos")
            
            print(f"\\n✅ IMPORTAÇÃO CONCLUÍDA: {inserted_count} registros")
            return inserted_count
            
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return 0

def verify_final_result():
    """Verificar resultado final"""
    print("\\n🔍 VERIFICAÇÃO FINAL...")
    print("=" * 30)
    
    try:
        with DatabaseSession() as session:
            # Contar registros
            result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
            total = result.fetchone()[0]
            
            # Listar colunas
            result = session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'financial_data'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"📊 Registros: {total}")
            print(f"📋 Colunas: {len(columns)}")
            
            print("\\nEstrutura final:")
            for i, (col_name, data_type) in enumerate(columns, 1):
                print(f"{i:2d}. {col_name:<20} | {data_type}")
            
            # Amostra de dados
            result = session.execute(text("SELECT * FROM financial_data LIMIT 2"))
            samples = result.fetchall()
            
            print("\\n📋 Amostra de dados:")
            col_names = [col[0] for col in columns]
            for i, sample in enumerate(samples, 1):
                print(f"\\nRegistro {i}:")
                for j, value in enumerate(sample):
                    if j < len(col_names):
                        print(f"  {col_names[j]}: {value}")
            
            return total
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal"""
    print("🚀 RECRIAÇÃO COMPLETA DA TABELA FINANCIAL_DATA")
    print("=" * 70)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # 1. Analisar Excel
    df, column_info = get_excel_columns()
    if df is None:
        sys.exit(1)
    
    # 2. Confirmar operação
    print("\\n⚠️  ATENÇÃO: Esta operação irá:")
    print("   • Excluir a tabela financial_data atual")
    print("   • Criar uma nova tabela com apenas as colunas do Excel")
    print("   • Importar todos os dados do Excel")
    print()
    
    # 3. Recriar tabela
    if not recreate_table_from_scratch(column_info):
        sys.exit(1)
    
    # 4. Importar dados
    imported = import_data(df, column_info)
    if imported == 0:
        print("❌ Falha na importação!")
        sys.exit(1)
    
    # 5. Verificar resultado
    final_count = verify_final_result()
    
    print("\\n" + "=" * 70)
    print("🎉 RECRIAÇÃO CONCLUÍDA!")
    print(f"📊 Excel: {len(df)} registros, {len(column_info)} colunas")
    print(f"📋 Tabela: {final_count} registros")
    print(f"✅ Status: {'SUCESSO' if imported == final_count else 'VERIFICAR'}")
    print("=" * 70)

if __name__ == "__main__":
    main()
