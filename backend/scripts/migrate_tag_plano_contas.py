#!/usr/bin/env python3
"""
Script para migrar o plano de contas da empresa TAG do Excel
Empresa: TAG (Business Solutions + Projetos)
Grupo: TAG (41054e58-53fb-4402-8ac1-a202f56bb8f5)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import uuid
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

def read_excel_plano_contas_tab(excel_path):
    """Lê a aba do plano de contas do Excel TAG"""
    try:
        print(f"📖 Lendo aba do plano de contas do Excel: {excel_path}")
        
        # Tentar diferentes nomes de aba
        possible_sheet_names = ['plano_de_contas', 'plano_contas', 'plano de contas', 'contas', 'planocontas']
        
        df = None
        sheet_name = None
        
        for name in possible_sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=name)
                sheet_name = name
                break
            except:
                continue
        
        if df is None:
            # Se não encontrar, listar todas as abas disponíveis
            xl = pd.ExcelFile(excel_path)
            print(f"❌ Aba do plano de contas não encontrada. Abas disponíveis:")
            for sheet in xl.sheet_names:
                print(f"  - {sheet}")
            return None
        
        print(f"✅ Aba '{sheet_name}' lida com sucesso!")
        print(f"📊 Total de linhas: {len(df):,}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler aba do plano de contas: {e}")
        return None

def analyze_plano_contas_data(df):
    """Analisa os dados do plano de contas antes da migração"""
    print("\n🔍 ANÁLISE DOS DADOS DO PLANO DE CONTAS ANTES DA MIGRAÇÃO...")
    print("=" * 60)
    
    # Estatísticas gerais
    print(f"📊 ESTATÍSTICAS GERAIS:")
    print(f"  - Total de linhas: {len(df):,}")
    print(f"  - Total de colunas: {len(df.columns)}")
    
    # Análise das colunas principais
    if 'conta_desc' in df.columns:
        contas = df['conta_desc'].value_counts().head(10)
        print(f"\n💰 TOP 10 CONTAS:")
        for conta, count in contas.items():
            print(f"  - {conta}: {count:,} registros")
    
    if 'para [conta]' in df.columns:
        contas_pai = df['para [conta]'].value_counts().head(10)
        print(f"\n🏗️ TOP 10 CONTAS PAI:")
        for conta, count in contas_pai.items():
            print(f"  - {conta}: {count:,} registros")
    
    # Verificar valores nulos
    for col in ['conta_desc', 'para [conta]', 'dre_n1', 'dre_n2', 'dfc_n1', 'dfc_n2']:
        if col in df.columns:
            nulos = df[col].isna().sum()
            print(f"\n📊 Valores nulos em '{col}': {nulos:,}")
    
    print("\n" + "=" * 60)

def clean_and_transform_plano_contas_data(df):
    """Limpa e transforma os dados do plano de contas do Excel"""
    print("\n🧹 LIMPANDO E TRANSFORMANDO DADOS DO PLANO DE CONTAS...")
    
    # Mapeamento de colunas Excel → Banco
    column_mapping = {
        'para [conta]': 'conta_pai',
        'conta_desc': 'nome_conta',
        'dre_n1': 'classificacao_dre',
        'dre_n2': 'classificacao_dre_n2',
        'dfc_n1': 'classificacao_dfc',
        'dfc_n2': 'classificacao_dfc_n2'
    }
    
    # Renomear colunas
    df_renamed = df.rename(columns=column_mapping)
    
    # Verificar colunas obrigatórias
    required_columns = ['nome_conta']
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
            print(f"    Linha {idx + 1}: 'nome_conta' = '{row['nome_conta'] if pd.notna(row['nome_conta']) else 'NULL'}'")
        if len(null_rows) > 5:
            print(f"    ... e mais {len(null_rows) - 5} linhas")
    
    # NÃO remover linhas com valores nulos - preservar TODAS as linhas
    df_clean = df_renamed.copy()
    
    print(f"  📊 Todas as {len(df_clean):,} linhas serão preservadas (incluindo com valores nulos)")
    print(f"  💡 Valores nulos serão convertidos para NULL no banco")
    
    # NÃO remover duplicatas - preservar TODAS as linhas do Excel
    df_clean = df_renamed.copy()
    
    print(f"  📊 Todas as {len(df_clean):,} linhas serão preservadas (incluindo duplicatas)")
    print(f"  💡 Duplicatas serão mantidas para preservar a estrutura original")
    
    return df_clean

def insert_plano_contas_data(conn, df_clean, grupo_empresa_id, empresa_ids):
    """Insere dados na tabela plano_de_contas - um registro para cada empresa"""
    print(f"\n💾 INSERINDO DADOS NA TABELA plano_de_contas...")
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
                        'empresa_id': empresa_id,
                        'grupo_empresa_id': grupo_empresa_id,
                        'conta_pai': row['conta_pai'] if pd.notna(row['conta_pai']) else None,
                        'nome_conta': row['nome_conta'],
                        'tipo_conta': None,  # Será preenchido posteriormente
                        'nivel': None,  # Será preenchido posteriormente
                        'ordem': None,  # Será preenchido posteriormente
                        'classificacao_dre': row['classificacao_dre'] if pd.notna(row['classificacao_dre']) else None,
                        'classificacao_dre_n2': row['classificacao_dre_n2'] if pd.notna(row['classificacao_dre_n2']) else None,
                        'classificacao_dfc': row['classificacao_dfc'] if pd.notna(row['classificacao_dfc']) else None,
                        'classificacao_dfc_n2': row['classificacao_dfc_n2'] if pd.notna(row['classificacao_dfc_n2']) else None,
                        'centro_custo': None,  # Será preenchido posteriormente
                        'observacoes': f'Migrado do Excel TAG - Empresa: {empresa_nome} - {datetime.now().strftime("%Y-%m-%d")}',
                        'is_active': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Query de inserção
                    insert_query = """
                        INSERT INTO plano_de_contas (
                            id, empresa_id, grupo_empresa_id, conta_pai, nome_conta, tipo_conta, nivel, ordem,
                            classificacao_dre, classificacao_dre_n2, classificacao_dfc, classificacao_dfc_n2,
                            centro_custo, observacoes, is_active, created_at, updated_at
                        ) VALUES (
                            %(id)s, %(empresa_id)s, %(grupo_empresa_id)s, %(conta_pai)s, %(nome_conta)s, %(tipo_conta)s,
                            %(nivel)s, %(ordem)s, %(classificacao_dre)s, %(classificacao_dre_n2)s,
                            %(classificacao_dfc)s, %(classificacao_dfc_n2)s, %(centro_custo)s, %(observacoes)s,
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

def validate_plano_contas_insertion(conn, grupo_empresa_id):
    """Valida os dados inseridos na tabela plano_de_contas"""
    print(f"\n🔍 VALIDANDO DADOS INSERIDOS NA TABELA plano_de_contas...")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Contar registros plano_de_contas da TAG
        validation_query = """
            SELECT 
                COUNT(*) as total_registros,
                COUNT(CASE WHEN nome_conta IS NOT NULL THEN 1 END) as com_nome,
                COUNT(CASE WHEN conta_pai IS NOT NULL THEN 1 END) as com_pai,
                COUNT(CASE WHEN classificacao_dre IS NOT NULL THEN 1 END) as com_dre,
                COUNT(CASE WHEN empresa_id IS NOT NULL THEN 1 END) as com_empresa_id
            FROM plano_de_contas 
            WHERE grupo_empresa_id = %s
        """
        
        cur.execute(validation_query, (grupo_empresa_id,))
        result = cur.fetchone()
        
        print(f"📊 VALIDAÇÃO DOS DADOS DO PLANO DE CONTAS INSERIDOS:")
        print("=" * 60)
        print(f"  📊 Total de registros: {result['total_registros']:,}")
        print(f"  💰 Com nome da conta: {result['com_nome']:,}")
        print(f"  🏗️ Com conta pai: {result['com_pai']:,}")
        print(f"  🏷️ Com classificação DRE: {result['com_dre']:,}")
        print(f"  🏢 Com empresa_id: {result['com_empresa_id']:,}")
        
        # Mostrar alguns exemplos
        examples_query = """
            SELECT nome_conta, conta_pai, classificacao_dre, empresa_id
            FROM plano_de_contas 
            WHERE grupo_empresa_id = %s
            LIMIT 5
        """
        
        cur.execute(examples_query, (grupo_empresa_id,))
        examples = cur.fetchall()
        
        print(f"\n📋 EXEMPLOS DE REGISTROS INSERIDOS:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. Nome: {example['nome_conta']}")
            print(f"     Pai: {example['conta_pai'] if example['conta_pai'] else 'NULL'}")
            print(f"     DRE: {example['classificacao_dre'] if example['classificacao_dre'] else 'NULL'}")
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
    print("🔄 MIGRANDO PLANO DE CONTAS DA EMPRESA TAG...")
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
        # 1. Ler Excel - aba plano de contas
        df = read_excel_plano_contas_tab(excel_path)
        if df is None:
            return
        
        # 2. Analisar dados antes da migração
        analyze_plano_contas_data(df)
        
        # 3. Limpar e transformar dados
        df_clean = clean_and_transform_plano_contas_data(df)
        if df_clean is None:
            return
        
        # 4. Inserir dados
        inserted_count = insert_plano_contas_data(conn, df_clean, grupo_empresa_id, empresa_ids)
        
        if inserted_count > 0:
            # 5. Validar inserção
            validate_plano_contas_insertion(conn, grupo_empresa_id)
            
            print(f"\n🎉 MIGRAÇÃO DO PLANO DE CONTAS CONCLUÍDA COM SUCESSO!")
            print(f"📊 {inserted_count:,} registros do plano de contas da empresa TAG inseridos")
            print(f"🔗 Dados disponíveis na tabela plano_de_contas")
            print(f"💡 Um registro criado para cada empresa (TAG Business Solutions + TAG Projetos)")
            print(f"⚠️ IMPORTANTE: FKs para DRE/DFC ainda não configuradas")
        else:
            print(f"\n❌ Nenhum registro do plano de contas foi inserido")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        conn.close()
        print("\n🎉 PROCESSO FINALIZADO!")

if __name__ == "__main__":
    main()
