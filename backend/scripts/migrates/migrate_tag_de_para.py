#!/usr/bin/env python3
"""
Script para migrar a aba "de_para" do Excel TAG para a tabela de_para
Empresa: TAG (Business Solutions + Projetos)
Grupo: TAG (41054e58-53fb-4402-8ac1-a202f56bb8f5)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import uuid
import json
from datetime import datetime
import os

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

def read_excel_de_para_tab(excel_path):
    """Lê a aba 'de_para' do Excel TAG"""
    try:
        print(f"📖 Lendo aba 'de_para' do Excel: {excel_path}")
        
        # Ler aba 'de_para'
        df = pd.read_excel(excel_path, sheet_name='de_para')
        
        print(f"✅ Aba 'de_para' lida com sucesso!")
        print(f"📊 Total de linhas: {len(df):,}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler aba 'de_para': {e}")
        return None

def analyze_de_para_data(df):
    """Analisa os dados da aba de_para antes da migração"""
    print("\n🔍 ANÁLISE DOS DADOS DE_PARA ANTES DA MIGRAÇÃO...")
    print("=" * 60)
    
    # Estatísticas gerais
    print(f"📊 ESTATÍSTICAS GERAIS:")
    print(f"  - Total de linhas: {len(df):,}")
    print(f"  - Total de colunas: {len(df.columns)}")
    
    # Análise das colunas principais
    if 'de [classificacao]' in df.columns:
        classificacoes = df['de [classificacao]'].value_counts().head(10)
        print(f"\n🏷️ TOP 10 CLASSIFICAÇÕES ORIGEM:")
        for classificacao, count in classificacoes.items():
            print(f"  - {classificacao}: {count:,} registros")
    
    if 'para [conta]' in df.columns:
        contas = df['para [conta]'].value_counts().head(10)
        print(f"\n💰 TOP 10 CONTAS DESTINO:")
        for conta, count in contas.items():
            print(f"  - {conta}: {count:,} registros")
    
    # Verificar valores nulos
    if 'de [classificacao]' in df.columns:
        nulos_origem = df['de [classificacao]'].isna().sum()
        print(f"\n📊 Valores nulos em 'de [classificacao]': {nulos_origem:,}")
    
    if 'para [conta]' in df.columns:
        nulos_destino = df['para [conta]'].isna().sum()
        print(f"\n📊 Valores nulos em 'para [conta]': {nulos_destino:,}")
    
    print("\n" + "=" * 60)

def clean_and_transform_de_para_data(df):
    """Limpa e transforma os dados de_para do Excel"""
    print("\n🧹 LIMPANDO E TRANSFORMANDO DADOS DE_PARA...")
    
    # Mapeamento de colunas Excel → Banco
    column_mapping = {
        'de [classificacao]': 'descricao_origem',
        'para [conta]': 'descricao_destino'
    }
    
    # Renomear colunas
    df_renamed = df.rename(columns=column_mapping)
    
    # Verificar colunas obrigatórias
    required_columns = ['descricao_origem', 'descricao_destino']
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
            origem_col = 'de [classificacao]' if 'de [classificacao]' in df_renamed.columns else 'descricao_origem'
            destino_col = 'para [conta]' if 'para [conta]' in df_renamed.columns else 'descricao_destino'
            origem_val = row[origem_col] if pd.notna(row[origem_col]) else 'NULL'
            destino_val = row[destino_col] if pd.notna(row[destino_col]) else 'NULL'
            print(f"    Linha {idx + 1}: 'de [classificacao]' = '{origem_val}', 'para [conta]' = '{destino_val}'")
        if len(null_rows) > 5:
            print(f"    ... e mais {len(null_rows) - 5} linhas")
    
    # NÃO remover linhas com valores nulos - preservar TODAS as linhas
    df_clean = df_renamed.copy()
    
    print(f"  📊 Todas as {len(df_clean):,} linhas serão preservadas (incluindo com valores nulos)")
    print(f"  💡 Valores nulos serão convertidos para NULL no banco")
    
    # Remover duplicatas baseado em descricao_origem e descricao_destino
    df_clean = df_clean.drop_duplicates(subset=['descricao_origem', 'descricao_destino'])
    final_count = len(df_clean)
    
    print(f"  📊 Linhas após remoção de duplicatas: {final_count:,}")
    print(f"  🗑️ Duplicatas removidas: {len(df_renamed) - final_count:,}")
    
    return df_clean

def insert_de_para_data(conn, df_clean, grupo_empresa_id, empresa_ids):
    """Insere dados na tabela de_para - um registro para cada empresa"""
    print(f"\n💾 INSERINDO DADOS NA TABELA de_para...")
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
                    insert_data = {
                        'id': record_id,
                        'empresa_id': empresa_id,  # ID específico de cada empresa
                        'grupo_empresa_id': grupo_empresa_id,
                        'origem_sistema': 'TAG_EXCEL',
                        'descricao_origem': row['descricao_origem'],
                        'descricao_destino': row['descricao_destino'],
                        'observacoes': f'Migrado do Excel TAG - Empresa: {empresa_nome} - {datetime.now().strftime("%Y-%m-%d")}',
                        'is_active': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Query de inserção
                    insert_query = """
                        INSERT INTO de_para (
                            id, empresa_id, grupo_empresa_id, origem_sistema, descricao_origem,
                            descricao_destino, observacoes, is_active, created_at, updated_at
                        ) VALUES (
                            %(id)s, %(empresa_id)s, %(grupo_empresa_id)s, %(origem_sistema)s,
                            %(descricao_origem)s, %(descricao_destino)s, %(observacoes)s,
                            %(is_active)s, %(created_at)s, %(updated_at)s
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

def validate_de_para_insertion(conn, grupo_empresa_id):
    """Valida os dados inseridos na tabela de_para"""
    print(f"\n🔍 VALIDANDO DADOS INSERIDOS NA TABELA de_para...")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Contar registros de_para da TAG
        validation_query = """
            SELECT 
                COUNT(*) as total_registros,
                COUNT(CASE WHEN descricao_origem IS NOT NULL THEN 1 END) as com_origem,
                COUNT(CASE WHEN descricao_destino IS NOT NULL THEN 1 END) as com_destino,
                COUNT(CASE WHEN empresa_id IS NOT NULL THEN 1 END) as com_empresa_id
            FROM de_para 
            WHERE grupo_empresa_id = %s
        """
        
        cur.execute(validation_query, (grupo_empresa_id,))
        result = cur.fetchone()
        
        print(f"📊 VALIDAÇÃO DOS DADOS DE_PARA INSERIDOS:")
        print("=" * 60)
        print(f"  📊 Total de registros: {result['total_registros']:,}")
        print(f"  🏷️ Com descrição origem: {result['com_origem']:,}")
        print(f"  💰 Com descrição destino: {result['com_destino']:,}")
        print(f"  🏢 Com empresa_id: {result['com_empresa_id']:,}")
        
        # Mostrar alguns exemplos
        examples_query = """
            SELECT descricao_origem, descricao_destino, empresa_id
            FROM de_para 
            WHERE grupo_empresa_id = %s
            LIMIT 5
        """
        
        cur.execute(examples_query, (grupo_empresa_id,))
        examples = cur.fetchall()
        
        print(f"\n📋 EXEMPLOS DE REGISTROS INSERIDOS:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. Origem: {example['descricao_origem']}")
            print(f"     Destino: {example['descricao_destino']}")
            print(f"     Empresas: {example['empresa_id']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
        
    finally:
        cur.close()

def main():
    """Função principal"""
    print("🔄 MIGRANDO DADOS DE_PARA DA EMPRESA TAG...")
    print("=" * 60)
    
    # Configurações
    excel_path = "db_TAG - Copia.xlsx"
    grupo_empresa_id = "41054e58-53fb-4402-8ac1-a202f56bb8f5"
    empresa_ids = get_tag_empresa_ids()
    
    print(f"📁 Arquivo Excel: {excel_path}")
    print(f"🏢 Grupo Empresa ID: {grupo_empresa_id}")
    print(f"🏢 Empresas TAG: {list(empresa_ids.keys())}")
    print(f"💡 Empresa_id será armazenado como JSON: {list(empresa_ids.values())}")
    print()
    
    # Verificar se arquivo existe
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo Excel não encontrado: {excel_path}")
        print("💡 Certifique-se de que o arquivo está no diretório backend/")
        return
    
    # Estabelecer conexão
    conn = get_connection()
    
    try:
        # 1. Ler Excel - aba de_para
        df = read_excel_de_para_tab(excel_path)
        if df is None:
            return
        
        # 2. Analisar dados antes da migração
        analyze_de_para_data(df)
        
        # 3. Limpar e transformar dados
        df_clean = clean_and_transform_de_para_data(df)
        if df_clean is None:
            return
        
        # 4. Inserir dados
        inserted_count = insert_de_para_data(conn, df_clean, grupo_empresa_id, empresa_ids)
        
        if inserted_count > 0:
            # 5. Validar inserção
            validate_de_para_insertion(conn, grupo_empresa_id)
            
            print(f"\n🎉 MIGRAÇÃO DE_PARA CONCLUÍDA COM SUCESSO!")
            print(f"📊 {inserted_count:,} registros de_para da empresa TAG inseridos")
            print(f"🔗 Dados disponíveis na tabela de_para")
            print(f"💡 Um registro criado para cada empresa (TAG Business Solutions + TAG Projetos)")
            print(f"⚠️ IMPORTANTE: FKs para plano_de_contas e DRE/DFC ainda não configuradas")
        else:
            print(f"\n❌ Nenhum registro de_para foi inserido")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        conn.close()
        print("\n🎉 PROCESSO FINALIZADO!")

if __name__ == "__main__":
    main()
