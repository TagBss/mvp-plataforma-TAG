#!/usr/bin/env python3
"""
Script para migrar dados da aba "dre_n1" do Excel para dre_structure_n1
"""

import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
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

def read_excel_dre_n1_tab():
    """Lê a aba "dre_n1" do Excel"""
    try:
        # Tentar diferentes nomes de aba
        sheet_names = ['dre_n1', 'dre-n1', 'dre n1', 'DRE N1', 'DRE_N1']
        
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel('db_TAG - Copia.xlsx', sheet_name=sheet_name)
                print(f"✅ Aba '{sheet_name}' lida com sucesso")
                return df
            except:
                continue
        
        # Se nenhuma das tentativas funcionou, tentar ler sem especificar aba
        df = pd.read_excel('db_TAG - Copia.xlsx')
        print("⚠️  Nenhuma aba específica encontrada, usando primeira aba")
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return None

def get_empresa_ids(conn):
    """Obtém os IDs das empresas TAG"""
    cur = conn.cursor()
    
    try:
        # Obter grupo_empresa_id da TAG
        cur.execute("""
            SELECT id FROM grupos_empresa WHERE nome = 'TAG'
        """)
        grupo_empresa_result = cur.fetchone()
        if not grupo_empresa_result:
            raise Exception("Grupo empresa 'TAG' não encontrado")
        
        grupo_empresa_id = grupo_empresa_result[0]
        
        # Obter empresa_ids das empresas TAG
        cur.execute("""
            SELECT id FROM empresas WHERE grupo_empresa_id = %s
        """, (grupo_empresa_id,))
        
        empresa_ids = [row[0] for row in cur.fetchall()]
        if not empresa_ids:
            raise Exception("Nenhuma empresa TAG encontrada")
        
        return grupo_empresa_id, empresa_ids
        
    finally:
        cur.close()

def extract_operation_type(description):
    """Extrai o tipo de operação da descrição"""
    if not description:
        return None
    
    # Padrões para extrair operation_type
    patterns = [
        r'^\s*\(\s*(\+)\s*\)',      # ( + )
        r'^\s*\(\s*(\-)\s*\)',      # ( - )
        r'^\s*\(\s*(\=)\s*\)',      # ( = )
        r'^\s*\(\s*(\+\s*\/\s*\-)\s*\)',  # ( + / - )
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            operation_type = match.group(1).strip()
            if operation_type == "+ / -":
                operation_type = "+/-"
            return operation_type
    
    return None

def clean_and_transform_dre_n1_data(df):
    """Limpa e transforma os dados do Excel"""
    print(f"📊 Dados originais: {len(df)} linhas")
    
    # Verificar colunas disponíveis
    print(f"📋 Colunas disponíveis: {list(df.columns)}")
    
    # Mapeamento de colunas (ajustar conforme necessário)
    column_mapping = {
        'dre_n1_id': 'dre_n1_id',  # order_index
        'dre_n1': 'dre_n1',        # description
    }
    
    # Renomear colunas se necessário
    df = df.rename(columns=column_mapping)
    
    # Manter todas as linhas, mesmo com valores nulos
    print(f"📊 Dados após limpeza: {len(df)} linhas")
    
    return df

def insert_dre_n1_structure_data(conn, df, grupo_empresa_id, empresa_ids):
    """Insere dados na tabela dre_structure_n1"""
    cur = conn.cursor()
    
    try:
        # Contar registros existentes para evitar duplicatas
        existing_count = 0
        for empresa_id in empresa_ids:
            cur.execute("""
                SELECT COUNT(*) FROM dre_structure_n1 
                WHERE empresa_id = %s
            """, (empresa_id,))
            existing_count += cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  Já existem {existing_count} registros para empresas TAG")
            response = input("Deseja continuar mesmo assim? (s/n): ")
            if response.lower() != 's':
                print("❌ Migração cancelada pelo usuário")
                return False
        
        # Inserir dados
        inserted_count = 0
        print(f"🔄 Iniciando inserção de {len(df)} linhas para {len(empresa_ids)} empresas...")
        
        for index, row in df.iterrows():
            print(f"  📝 Processando linha {index + 1}: {row['dre_n1']}")
            
            for empresa_id in empresa_ids:
                record_id = str(uuid.uuid4())
                
                # Tratar a coluna name removendo sinais operadores da description
                description = row['dre_n1'] if pd.notna(row['dre_n1']) else None
                name = "Sem descrição"  # Valor padrão para evitar NULL
                operation_type = None
                
                if description:
                    # Extrair operation_type
                    operation_type = extract_operation_type(description)
                    
                    # Remover sinais operadores para o name
                    name = re.sub(r'^\s*\([^)]+\)\s*', '', description).strip()
                    
                    # Se após remover os operadores ficar vazio, usar valor padrão
                    if not name:
                        name = "Sem descrição"
                
                insert_data = {
                    'id': record_id,
                    'empresa_id': empresa_id,
                    'grupo_empresa_id': grupo_empresa_id,
                    'order_index': row['dre_n1_id'] if pd.notna(row['dre_n1_id']) else None,
                    'description': description,
                    'name': name,
                    'operation_type': operation_type,
                    'is_active': True,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                print(f"    🏢 Empresa ID: {empresa_id}")
                print(f"    📊 Order Index: {insert_data['order_index']}")
                print(f"    📝 Name: {insert_data['name']}")
                print(f"    🔧 Operation Type: {insert_data['operation_type']}")
                
                insert_query = """
                    INSERT INTO dre_structure_n1 (
                        id, empresa_id, grupo_empresa_id, order_index, description, name, 
                        operation_type, is_active, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(empresa_id)s, %(grupo_empresa_id)s, %(order_index)s, 
                        %(description)s, %(name)s, %(operation_type)s, %(is_active)s, 
                        %(created_at)s, %(updated_at)s
                    )
                """
                
                try:
                    cur.execute(insert_query, insert_data)
                    inserted_count += 1
                    print(f"    ✅ Inserido com sucesso (total: {inserted_count})")
                except Exception as e:
                    print(f"    ❌ Erro ao inserir: {e}")
                    raise e
        
        # Fazer commit da transação
        conn.commit()
        print(f"✅ {inserted_count} registros inseridos com sucesso")
        print(f"✅ Transação commitada com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        return False
        
    finally:
        cur.close()

def main():
    """Função principal"""
    print("🚀 MIGRANDO DADOS DA ABA 'dre_n1' PARA dre_structure_n1...")
    print("=" * 70)
    
    # Ler Excel
    df = read_excel_dre_n1_tab()
    if df is None:
        return
    
    print(f"📊 Dados lidos: {len(df)} linhas")
    
    # Conectar ao banco
    conn = get_connection()
    
    try:
        # Obter IDs das empresas
        grupo_empresa_id, empresa_ids = get_empresa_ids(conn)
        print(f"🏢 Grupo empresa ID: {grupo_empresa_id}")
        print(f"🏢 Empresas IDs: {empresa_ids}")
        
        # Limpar e transformar dados
        df_clean = clean_and_transform_dre_n1_data(df)
        
        # Inserir dados
        if insert_dre_n1_structure_data(conn, df_clean, grupo_empresa_id, empresa_ids):
            print("🎉 Migração concluída com sucesso!")
        else:
            print("❌ Migração falhou")
            
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
