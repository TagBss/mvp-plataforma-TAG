#!/usr/bin/env python3
"""
Script para migrar a aba "dre" do Excel TAG para a tabela dre_structure_n0
Empresa: TAG (Business Solutions + Projetos)
Grupo: TAG (41054e58-53fb-4402-8ac1-a202f56bb8f5)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import uuid
from datetime import datetime
import os
import re

def get_connection():
    """Estabelece conexão com o banco"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='tag_financeiro',
        user='postgres',
        password='postgres'
    )

def get_tag_empresa_ids():
    """IDs das empresas TAG"""
    return {
        "TAG Business Solutions": "d09c3591-3de3-4a8f-913a-2e36de84610f",
        "TAG Projetos": "7c0c1321-d065-4ed2-afbf-98b2524892ac"
    }

def read_excel_dre_tab(excel_path):
    """Lê a aba 'dre' do Excel TAG"""
    try:
        print(f"📖 Lendo aba 'dre' do Excel: {excel_path}")
        
        # Ler aba 'dre'
        df = pd.read_excel(excel_path, sheet_name='dre')
        
        print(f"✅ Aba 'dre' lida com sucesso!")
        print(f"📊 Total de linhas: {len(df):,}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler aba 'dre': {e}")
        return None

def analyze_dre_data(df):
    """Analisa os dados da aba dre antes da migração"""
    print("\n🔍 ANÁLISE DOS DADOS DRE ANTES DA MIGRAÇÃO...")
    print("=" * 60)
    
    # Estatísticas gerais
    print(f"📊 ESTATÍSTICAS GERAIS:")
    print(f"  - Total de linhas: {len(df):,}")
    print(f"  - Total de colunas: {len(df.columns)}")
    
    # Análise das colunas principais
    if 'dre' in df.columns:
        descriptions = df['dre'].value_counts().head(10)
        print(f"\n📋 TOP 10 DESCRIÇÕES DRE:")
        for desc, count in descriptions.items():
            print(f"  - {desc}: {count:,} registros")
    
    if 'dre_n0_ordem' in df.columns:
        ordens = df['dre_n0_ordem'].value_counts().head(10)
        print(f"\n🔢 TOP 10 ORDENS DRE:")
        for ordem, count in ordens.items():
            print(f"  - {ordem}: {count:,} registros")
    
    if 'dre_niveis' in df.columns:
        niveis = df['dre_niveis'].value_counts().head(10)
        print(f"\n🏗️ TOP 10 NÍVEIS DRE:")
        for nivel, count in niveis.items():
            print(f"  - {nivel}: {count:,} registros")
    
    # Verificar valores nulos
    for col in ['dre', 'dre_n0_ordem', 'dre_niveis']:
        if col in df.columns:
            nulos = df[col].isna().sum()
            print(f"\n📊 Valores nulos em '{col}': {nulos:,}")
    
    print("\n" + "=" * 60)

def clean_and_transform_dre_data(df):
    """Limpa e transforma os dados dre do Excel"""
    print("\n🧹 LIMPANDO E TRANSFORMANDO DADOS DRE...")
    
    # Mapeamento de colunas Excel → Banco
    column_mapping = {
        'dre_n0_ordem': 'dre_n0_ordem',  # Mesmo nome
        'dre': 'description',  # dre → description
        'dre_niveis': 'dre_niveis'  # Mesmo nome
    }
    
    # Renomear colunas
    df_renamed = df.rename(columns=column_mapping)
    
    # Verificar colunas obrigatórias
    required_columns = ['description', 'dre_n0_ordem']
    missing_columns = [col for col in required_columns if col not in df_renamed.columns]
    
    if missing_columns:
        print(f"❌ Colunas obrigatórias não encontradas: {missing_columns}")
        return None
    
    # Mostrar linhas com valores nulos (mas NÃO remover)
    print(f"  📊 Linhas iniciais: {len(df_renamed):,}")
    
    # Verificar valores nulos
    null_rows = df_renamed[df_renamed.isnull().any(axis=1)]
    if len(null_rows) > 0:
        print(f"  ⚠️ Linhas com valores nulos encontradas (serão preservadas):")
        for idx, row in null_rows.head(5).iterrows():
            print(f"    Linha {idx + 1}: 'description' = '{row['description'] if pd.notna(row['description']) else 'NULL'}'")
        if len(null_rows) > 5:
            print(f"    ... e mais {len(null_rows) - 5} linhas")
    
    # NÃO remover linhas com valores nulos - preservar TODAS as linhas
    df_clean = df_renamed.copy()
    
    print(f"  📊 Todas as {len(df_clean):,} linhas serão preservadas (incluindo com valores nulos)")
    print(f"  💡 Valores nulos serão convertidos para NULL no banco")
    
    # NÃO remover duplicatas - preservar TODAS as linhas do Excel
    print(f"  📊 Todas as {len(df_clean):,} linhas serão preservadas (incluindo duplicatas)")
    print(f"  💡 Duplicatas serão mantidas para preservar a estrutura original")
    
    return df_clean

def insert_dre_structure_data(conn, df_clean, grupo_empresa_id, empresa_ids):
    """Insere dados na tabela dre_structure_n0 - um registro para cada empresa"""
    print(f"\n💾 INSERINDO DADOS NA TABELA dre_structure_n0...")
    print(f"💡 Criando um registro para cada empresa (TAG Business Solutions + TAG Projetos)")
    
    cur = conn.cursor()
    
    try:
        # Contadores
        total_rows = len(df_clean)
        inserted_rows = 0
        error_rows = 0
        
        print(f"📊 Total de linhas Excel: {total_rows:,}")
        print(f"📊 Total de registros a inserir: {total_rows * len(empresa_ids):,} (2 por linha)")
        
        for index, row in df_clean.iterrows():
            try:
                # Para cada linha do Excel, criar um registro para cada empresa
                for empresa_nome, empresa_id in empresa_ids.items():
                    # Gerar UUID único para cada registro
                    record_id = str(uuid.uuid4())
                    
                    # Preparar dados para inserção
                    # Tratar a coluna name removendo sinais operadores da description
                    description = row['description']
                    name = description
                    if description:
                        # Remover sinais operadores como ( + ), ( - ), ( = ), ( + / - )
                        name = re.sub(r'^\s*\([^)]+\)\s*', '', description).strip()
                    
                    insert_data = {
                        'id': record_id,
                        'empresa_id': empresa_id,
                        'grupo_empresa_id': grupo_empresa_id,
                        'dre_n0_ordem': row['dre_n0_ordem'] if pd.notna(row['dre_n0_ordem']) else None,
                        'description': row['description'],
                        'name': name,
                        'dre_niveis': row['dre_niveis'] if pd.notna(row['dre_niveis']) else None,
                        'is_active': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Query de inserção
                    insert_query = """
                        INSERT INTO dre_structure_n0 (
                            id, empresa_id, grupo_empresa_id, dre_n0_ordem, description, name, dre_niveis,
                            is_active, created_at, updated_at
                        ) VALUES (
                            %(id)s, %(empresa_id)s, %(grupo_empresa_id)s, %(dre_n0_ordem)s, %(description)s,
                            %(name)s, %(dre_niveis)s, %(is_active)s, %(created_at)s, %(updated_at)s
                        )
                    """
                    
                    cur.execute(insert_query, insert_data)
                    inserted_rows += 1
                
                # Progresso a cada 50 linhas Excel (100 registros inseridos)
                if (index + 1) % 50 == 0:
                    print(f"  📊 Progresso: {index + 1:,}/{total_rows:,} linhas Excel processadas ({inserted_rows:,} registros inseridos)")
                
            except Exception as e:
                print(f"  ❌ Erro ao processar linha {index}: {e}")
                error_rows += 1
                continue
        
        # Commit das alterações
        conn.commit()
        
        print(f"\n✅ INSERÇÃO CONCLUÍDA!")
        print(f"📊 Total inserido: {inserted_rows:,} registros")
        print(f"❌ Erros: {error_rows} registros")
        print(f"📈 Taxa de sucesso: {(inserted_rows/(total_rows * len(empresa_ids)))*100:.1f}%")
        
        return inserted_rows
        
    except Exception as e:
        print(f"❌ Erro geral na inserção: {e}")
        conn.rollback()
        return 0
        
    finally:
        cur.close()

def validate_dre_structure_insertion(conn, grupo_empresa_id):
    """Valida os dados inseridos na tabela dre_structure_n0"""
    print(f"\n🔍 VALIDANDO DADOS INSERIDOS NA TABELA dre_structure_n0...")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Contar registros dre_structure_n0 da TAG
        validation_query = """
            SELECT 
                COUNT(*) as total_registros,
                COUNT(CASE WHEN description IS NOT NULL THEN 1 END) as com_description,
                COUNT(CASE WHEN dre_n0_ordem IS NOT NULL THEN 1 END) as com_ordem,
                COUNT(CASE WHEN dre_niveis IS NOT NULL THEN 1 END) as com_niveis,
                COUNT(CASE WHEN empresa_id IS NOT NULL THEN 1 END) as com_empresa_id
            FROM dre_structure_n0 
            WHERE grupo_empresa_id = %s
        """
        
        cur.execute(validation_query, (grupo_empresa_id,))
        result = cur.fetchone()
        
        print(f"📊 VALIDAÇÃO DOS DADOS DRE_STRUCTURE_N0 INSERIDOS:")
        print("=" * 60)
        print(f"  📊 Total de registros: {result['total_registros']:,}")
        print(f"  📋 Com description: {result['com_description']:,}")
        print(f"  🔢 Com ordem: {result['com_ordem']:,}")
        print(f"  🏗️ Com níveis: {result['com_niveis']:,}")
        print(f"  🏢 Com empresa_id: {result['com_empresa_id']:,}")
        
        # Mostrar alguns exemplos
        examples_query = """
            SELECT dre_n0_ordem, description, dre_niveis, empresa_id
            FROM dre_structure_n0 
            WHERE grupo_empresa_id = %s
            LIMIT 5
        """
        
        cur.execute(examples_query, (grupo_empresa_id,))
        examples = cur.fetchall()
        
        print(f"\n📋 EXEMPLOS DE REGISTROS INSERIDOS:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. Ordem: {example['dre_n0_ordem'] if example['dre_n0_ordem'] else 'NULL'}")
            print(f"     Description: {example['description']}")
            print(f"     Níveis: {example['dre_niveis'] if example['dre_niveis'] else 'NULL'}")
            print(f"     Empresa: {example['empresa_id']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
        
    finally:
        cur.close()

def main():
    """Função principal"""
    print("🔄 MIGRANDO ESTRUTURA DRE DA EMPRESA TAG...")
    print("=" * 60)
    
    # Configurações
    excel_path = "db_TAG - Copia.xlsx"
    grupo_empresa_id = "41054e58-53fb-4402-8ac1-a202f56bb8f5"
    empresa_ids = get_tag_empresa_ids()
    
    print(f"📁 Arquivo Excel: {excel_path}")
    print(f"🏢 Grupo Empresa ID: {grupo_empresa_id}")
    print(f"🏢 Empresas TAG: {list(empresa_ids.keys())}")
    print()
    
    # Verificar se arquivo existe
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo Excel não encontrado: {excel_path}")
        print("💡 Certifique-se de que o arquivo está no diretório backend/")
        return
    
    # Estabelecer conexão
    conn = get_connection()
    
    try:
        # 1. Ler Excel - aba dre
        df = read_excel_dre_tab(excel_path)
        if df is None:
            return
        
        # 2. Analisar dados antes da migração
        analyze_dre_data(df)
        
        # 3. Limpar e transformar dados
        df_clean = clean_and_transform_dre_data(df)
        if df_clean is None:
            return
        
        # 4. Inserir dados
        inserted_count = insert_dre_structure_data(conn, df_clean, grupo_empresa_id, empresa_ids)
        
        if inserted_count > 0:
            # 5. Validar inserção
            validate_dre_structure_insertion(conn, grupo_empresa_id)
            
            print(f"\n🎉 MIGRAÇÃO DA ESTRUTURA DRE CONCLUÍDA COM SUCESSO!")
            print(f"📊 {inserted_count:,} registros da estrutura DRE da empresa TAG inseridos")
            print(f"🔗 Dados disponíveis na tabela dre_structure_n0")
            print(f"💡 Um registro criado para cada empresa (TAG Business Solutions + TAG Projetos)")
        else:
            print(f"\n❌ Nenhum registro da estrutura DRE foi inserido")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        conn.close()
        print("\n🎉 PROCESSO FINALIZADO!")

if __name__ == "__main__":
    main()
