#!/usr/bin/env python3
"""
Script para adicionar colunas faltantes na tabela financial_data
baseado na estrutura do Excel na aba 'base'
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys

def check_current_structure():
    """Verificar estrutura atual da tabela"""
    print("🔍 Verificando estrutura atual da tabela financial_data...")
    
    with DatabaseSession() as session:
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'financial_data'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print(f"📊 Colunas atuais ({len(columns)}):")
        for col_name, data_type, is_nullable in columns:
            print(f"  - {col_name}: {data_type}")
        
        return [col[0] for col in columns]

def add_missing_columns():
    """Adicionar colunas faltantes"""
    print("\n🔧 Adicionando colunas faltantes...")
    
    current_columns = check_current_structure()
    
    # Colunas que precisam ser adicionadas
    columns_to_add = []
    
    # Verificar se as colunas de data existem
    date_columns = {
        'emissao': 'DATE',
        'competencia': 'DATE', 
        'vencimento': 'DATE'
    }
    
    for col_name, col_type in date_columns.items():
        if col_name not in current_columns:
            columns_to_add.append((col_name, col_type))
    
    # Verificar se as colunas de mapeamento existem
    mapping_columns = {
        'dfc_n1': 'TEXT',
        'dfc_n2': 'TEXT',
        'origem': 'TEXT'
    }
    
    for col_name, col_type in mapping_columns.items():
        if col_name not in current_columns:
            columns_to_add.append((col_name, col_type))
    
    if not columns_to_add:
        print("✅ Todas as colunas necessárias já existem!")
        return
    
    # Adicionar as colunas
    with DatabaseSession() as session:
        for col_name, col_type in columns_to_add:
            print(f"  ➕ Adicionando coluna: {col_name} ({col_type})")
            session.execute(text(f"ALTER TABLE financial_data ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
        
        session.commit()
        print("✅ Colunas adicionadas com sucesso!")

def populate_columns_from_excel():
    """Popular as novas colunas com dados do Excel"""
    print("\n📥 Populando colunas com dados do Excel...")
    
    # Ler dados do Excel
    try:
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        print(f"📊 Lidos {len(df)} registros do Excel")
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return
    
    # Verificar se temos as colunas necessárias no Excel
    required_cols = ['emissao', 'competencia', 'vencimento', 'dfc_n1', 'dfc_n2', 'origem']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"⚠️  Colunas faltantes no Excel: {missing_cols}")
        return
    
    with DatabaseSession() as session:
        # Verificar se podemos mapear pelos IDs ou precisamos usar outros campos
        result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
        db_count = result.fetchone()[0]
        
        if db_count != len(df):
            print(f"⚠️  Contagem diferente: DB={db_count}, Excel={len(df)}")
            print("   Usando mapeamento por ID...")
            
            # Mapear por ID se disponível
            if 'id' in df.columns:
                for _, row in df.iterrows():
                    update_sql = text("""
                        UPDATE financial_data 
                        SET 
                            emissao = :emissao,
                            competencia = :competencia,
                            vencimento = :vencimento,
                            dfc_n1 = :dfc_n1,
                            dfc_n2 = :dfc_n2,
                            origem = :origem
                        WHERE id = :id
                    """)
                    
                    session.execute(update_sql, {
                        'id': row.get('id'),
                        'emissao': row['emissao'],
                        'competencia': row['competencia'],
                        'vencimento': row['vencimento'],
                        'dfc_n1': row['dfc_n1'],
                        'dfc_n2': row['dfc_n2'],
                        'origem': row['origem']
                    })
            else:
                print("❌ Não foi possível mapear - coluna ID não encontrada")
                return
        else:
            print("   Atualizando todos os registros em ordem...")
            
            # Se as contagens batem, atualizar em ordem
            result = session.execute(text("SELECT id FROM financial_data ORDER BY id"))
            db_ids = [row[0] for row in result.fetchall()]
            
            for i, (_, row) in enumerate(df.iterrows()):
                if i < len(db_ids):
                    update_sql = text("""
                        UPDATE financial_data 
                        SET 
                            emissao = :emissao,
                            competencia = :competencia,
                            vencimento = :vencimento,
                            dfc_n1 = :dfc_n1,
                            dfc_n2 = :dfc_n2,
                            origem = :origem
                        WHERE id = :id
                    """)
                    
                    session.execute(update_sql, {
                        'id': db_ids[i],
                        'emissao': row['emissao'],
                        'competencia': row['competencia'],
                        'vencimento': row['vencimento'],
                        'dfc_n1': row['dfc_n1'],
                        'dfc_n2': row['dfc_n2'],
                        'origem': row['origem']
                    })
        
        session.commit()
        print("✅ Dados populados com sucesso!")

def verify_update():
    """Verificar se a atualização foi bem-sucedida"""
    print("\n🔍 Verificando atualização...")
    
    with DatabaseSession() as session:
        # Verificar estrutura final
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financial_data'
            ORDER BY ordinal_position
        """))
        
        columns = [row[0] for row in result.fetchall()]
        print(f"📊 Estrutura final ({len(columns)} colunas):")
        for col in columns:
            print(f"  - {col}")
        
        # Verificar dados de amostra
        result = session.execute(text("""
            SELECT 
                id, 
                emissao, 
                competencia, 
                vencimento, 
                data,
                dfc_n1, 
                dfc_n2, 
                origem,
                category,
                subcategory,
                source
            FROM financial_data 
            WHERE emissao IS NOT NULL 
            LIMIT 3
        """))
        
        sample_data = result.fetchall()
        print(f"\n📋 Amostra de dados atualizados:")
        for i, row in enumerate(sample_data):
            print(f"  Registro {i+1}:")
            print(f"    ID: {row[0]}")
            print(f"    Emissão: {row[1]}")
            print(f"    Competência: {row[2]}")
            print(f"    Vencimento: {row[3]}")
            print(f"    Data: {row[4]}")
            print(f"    DFC N1: {row[5]}")
            print(f"    DFC N2: {row[6]}")
            print(f"    Origem: {row[7]}")
            print(f"    Category (antigo): {row[8]}")
            print(f"    Subcategory (antigo): {row[9]}")
            print(f"    Source (antigo): {row[10]}")

def main():
    """Função principal"""
    print("🚀 Iniciando adição de colunas faltantes...")
    
    try:
        # 1. Verificar estrutura atual
        check_current_structure()
        
        # 2. Adicionar colunas faltantes
        add_missing_columns()
        
        # 3. Popular com dados do Excel
        populate_columns_from_excel()
        
        # 4. Verificar resultado
        verify_update()
        
        print("\n🎉 Processo concluído com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o processo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
