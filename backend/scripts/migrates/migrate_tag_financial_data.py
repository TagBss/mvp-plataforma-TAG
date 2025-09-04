#!/usr/bin/env python3
"""
Script para migrar dados da aba "base" do Excel TAG para financial_data
Empresa: TAG (Business Solutions ou Projetos)
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

def get_tag_empresa_mapping():
    """Mapeamento de empresas TAG para IDs"""
    return {
        "TAG Business Solutions": "d09c3591-3de3-4a8f-913a-2e36de84610f",
        "TAG Projetos": "7c0c1321-d065-4ed2-afbf-98b2524892ac"
    }

def read_excel_base_tab(excel_path):
    """Lê a aba 'base' do Excel TAG"""
    try:
        print(f"📖 Lendo Excel: {excel_path}")
        
        # Ler aba 'base'
        df = pd.read_excel(excel_path, sheet_name='base')
        
        print(f"✅ Excel lido com sucesso!")
        print(f"📊 Total de linhas: {len(df):,}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return None

def analyze_data_before_migration(df):
    """Analisa os dados antes da migração para identificar possíveis problemas"""
    print("\n🔍 ANÁLISE DOS DADOS ANTES DA MIGRAÇÃO...")
    print("=" * 60)
    
    # Estatísticas gerais
    print(f"📊 ESTATÍSTICAS GERAIS:")
    print(f"  - Total de linhas: {len(df):,}")
    print(f"  - Total de colunas: {len(df.columns)}")
    
    # Análise por empresa
    if 'empresa' in df.columns:
        empresas = df['empresa'].value_counts()
        print(f"\n🏢 DISTRIBUIÇÃO POR EMPRESA:")
        for empresa, count in empresas.items():
            print(f"  - {empresa}: {count:,} registros")
    
    # Análise de valores
    if 'valor_original' in df.columns:
        valor_total = df['valor_original'].sum()
        valor_medio = df['valor_original'].mean()
        print(f"\n💰 ANÁLISE DE VALORES:")
        print(f"  - Valor total: R$ {valor_total:,.2f}")
        print(f"  - Valor médio: R$ {valor_total/len(df):,.2f}")
        print(f"  - Valores nulos: {df['valor_original'].isna().sum():,}")
    
    # Análise de datas
    date_columns = ['emissao', 'competencia', 'vencimento', 'data']
    for col in date_columns:
        if col in df.columns:
            print(f"\n📅 ANÁLISE DA COLUNA '{col}':")
            print(f"  - Valores únicos: {df[col].nunique():,}")
            print(f"  - Valores nulos: {df[col].isna().sum():,}")
            if df[col].dtype == 'object':
                print(f"  - Exemplos: {df[col].dropna().head(3).tolist()}")
    
    # Análise de classificações
    if 'de [classificacao]' in df.columns:
        classificacoes = df['de [classificacao]'].value_counts().head(10)
        print(f"\n🏷️ TOP 10 CLASSIFICAÇÕES:")
        for classificacao, count in classificacoes.items():
            print(f"  - {classificacao}: {count:,} registros")
    
    print("\n" + "=" * 60)

def clean_and_transform_data(df):
    """Limpa e transforma os dados do Excel"""
    print("\n🧹 LIMPANDO E TRANSFORMANDO DADOS...")
    
    # Mapeamento de colunas Excel → Banco
    column_mapping = {
        'emissao': 'emissao',
        'competencia': 'competencia', 
        'vencimento': 'vencimento',
        'origem': 'origem',
        'empresa': 'empresa',
        'nome': 'nome',
        'de [classificacao]': 'classificacao',  # Coluna específica do Excel
        'valor_original': 'valor_original',
        'data': 'data',
        'valor': 'valor',
        'banco': 'banco',
        'conta corrente': 'conta_corrente',  # Corrigido: Excel tem "conta corrente"
        'centro de resultado': 'centro_de_resultado',  # Adicionado: Excel tem "centro de resultado"
        'observação': 'observacao'  # Adicionado: Excel tem "observação"
    }
    
    # Renomear colunas
    df_renamed = df.rename(columns=column_mapping)
    
    # Verificar colunas obrigatórias
    required_columns = ['emissao', 'competencia', 'origem', 'empresa', 'classificacao', 'valor_original']
    missing_columns = [col for col in required_columns if col not in df_renamed.columns]
    
    if missing_columns:
        print(f"❌ Colunas obrigatórias não encontradas: {missing_columns}")
        return None
    
    # Limpar dados - NÃO remover linhas com valores nulos
    df_clean = df_renamed.copy()
    
    # Apenas substituir valores nulos por None (não remover linhas)
    initial_count = len(df_clean)
    
    print(f"  📊 Total de linhas: {initial_count:,}")
    print(f"  📊 Todas as linhas serão inseridas (incluindo com valores nulos)")
    print(f"  ⚠️ Valores nulos serão convertidos para NULL no banco")
    
    # Converter tipos de dados
    try:
        # Datas
        date_columns = ['emissao', 'competencia', 'vencimento', 'data']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        
        # Valores numéricos
        numeric_columns = ['valor_original', 'valor']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        print("  ✅ Tipos de dados convertidos com sucesso")
        
    except Exception as e:
        print(f"  ❌ Erro ao converter tipos de dados: {e}")
        return None
    
    return df_clean

def insert_batch(cur, batch_data):
    """Insere um lote de dados usando executemany para melhor performance"""
    try:
        # Query de inserção otimizada
        insert_query = """
            INSERT INTO financial_data (
                id, emissao, competencia, vencimento, origem, empresa, nome, 
                classificacao, valor_original, data, valor, banco, conta_corrente,
                centro_de_resultado, observacao, grupo_empresa_id, empresa_id, 
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        cur.executemany(insert_query, batch_data)
        return len(batch_data)
        
    except Exception as e:
        print(f"  ❌ Erro ao inserir lote: {e}")
        return 0

def insert_financial_data(conn, df_clean, grupo_empresa_id, empresa_mapping):
    """Insere dados na tabela financial_data usando batch insert para melhor performance"""
    print(f"\n💾 INSERINDO DADOS NA TABELA financial_data...")
    
    cur = conn.cursor()
    
    try:
        # Contadores
        total_rows = len(df_clean)
        inserted_rows = 0
        error_rows = 0
        
        print(f"📊 Total de linhas para inserir: {total_rows:,}")
        print(f"⚡ Usando inserção em lotes para melhor performance")
        
        # Tamanho do lote para inserção
        batch_size = 1000
        current_batch = []
        
        for index, row in df_clean.iterrows():
            try:
                # Gerar UUID único
                record_id = str(uuid.uuid4())
                
                # Mapear empresa para ID
                empresa_nome = row['empresa']
                empresa_id = empresa_mapping.get(empresa_nome)
                
                if not empresa_id:
                    print(f"  ⚠️ Empresa não mapeada: {empresa_nome}")
                    error_rows += 1
                    continue
                
                # Preparar dados para inserção
                insert_data = (
                    record_id,
                    row['emissao'] if pd.notna(row['emissao']) else None,
                    row['competencia'] if pd.notna(row['competencia']) else None,
                    row['vencimento'] if pd.notna(row['vencimento']) else None,
                    row['origem'] if pd.notna(row['origem']) else None,
                    row['empresa'] if pd.notna(row['empresa']) else None,
                    row['nome'] if pd.notna(row['nome']) else None,
                    row['classificacao'] if pd.notna(row['classificacao']) else None,
                    row['valor_original'] if pd.notna(row['valor_original']) else None,
                    row['data'] if pd.notna(row['data']) else None,
                    row['valor'] if pd.notna(row['valor']) else None,
                    row['banco'] if pd.notna(row['banco']) else None,
                    row['conta_corrente'] if pd.notna(row['conta_corrente']) else None,
                    row['centro_de_resultado'] if pd.notna(row['centro_de_resultado']) else None,
                    row['observacao'] if pd.notna(row['observacao']) else None,
                    grupo_empresa_id,
                    empresa_id,
                    datetime.now(),
                    datetime.now()
                )
                
                current_batch.append(insert_data)
                
                # Inserir lote quando atingir o tamanho
                if len(current_batch) >= batch_size:
                    inserted_rows += insert_batch(cur, current_batch)
                    current_batch = []
                    
                    # Progresso
                    print(f"  📊 Progresso: {inserted_rows:,}/{total_rows:,} registros inseridos")
            except Exception as e:
                print(f"  ❌ Erro ao processar linha {index}: {e}")
                error_rows += 1
                continue
        
        # Inserir lote restante
        if current_batch:
            inserted_rows += insert_batch(cur, current_batch)
        
        # Commit das alterações
        conn.commit()
        
        print(f"\n✅ INSERÇÃO CONCLUÍDA!")
        print(f"📊 Total inserido: {inserted_rows:,} registros")
        print(f"❌ Erros: {error_rows} registros")
        print(f"📈 Taxa de sucesso: {(inserted_rows/total_rows)*100:.1f}%")
        
        return inserted_rows
        
    except Exception as e:
        print(f"❌ Erro geral na inserção: {e}")
        conn.rollback()
        return 0
        
    finally:
        cur.close()

def validate_insertion(conn, grupo_empresa_id):
    """Valida os dados inseridos"""
    print(f"\n🔍 VALIDANDO DADOS INSERIDOS...")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Contar registros por empresa TAG
        validation_query = """
            SELECT 
                empresa,
                COUNT(*) as total_registros,
                COUNT(CASE WHEN valor_original IS NOT NULL THEN 1 END) as com_valor,
                MIN(competencia) as competencia_min,
                MAX(competencia) as competencia_max,
                SUM(valor_original) as valor_total
            FROM financial_data 
            WHERE grupo_empresa_id = %s
            GROUP BY empresa
            ORDER BY empresa
        """
        
        cur.execute(validation_query, (grupo_empresa_id,))
        results = cur.fetchall()
        
        print(f"📊 VALIDAÇÃO DOS DADOS INSERIDOS:")
        print("=" * 60)
        
        total_records = 0
        total_value = 0
        
        for row in results:
            print(f"🏢 {row['empresa']}:")
            print(f"  📊 Total de registros: {row['total_registros']:,}")
            print(f"  💰 Registros com valor: {row['com_valor']:,}")
            print(f"  📅 Período: {row['competencia_min']} a {row['competencia_max']}")
            print(f"  💵 Valor total: R$ {row['valor_total']:,.2f}")
            print()
            
            total_records += row['total_registros']
            total_value += row['valor_total'] or 0
        
        print(f"📈 RESUMO GERAL:")
        print(f"  📊 Total de registros TAG: {total_records:,}")
        print(f"  💰 Valor total TAG: R$ {total_value:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
        
    finally:
        cur.close()

def main():
    """Função principal"""
    print("🔄 MIGRANDO DADOS FINANCEIROS DA EMPRESA TAG...")
    print("=" * 60)
    
    # Configurações
    excel_path = "db_TAG - Copia.xlsx"
    grupo_empresa_id = "41054e58-53fb-4402-8ac1-a202f56bb8f5"
    empresa_mapping = get_tag_empresa_mapping()
    
    print(f"📁 Arquivo Excel: {excel_path}")
    print(f"🏢 Grupo Empresa ID: {grupo_empresa_id}")
    print(f"🏢 Empresas TAG: {list(empresa_mapping.keys())}")
    print()
    
    # Verificar se arquivo existe
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo Excel não encontrado: {excel_path}")
        print("💡 Certifique-se de que o arquivo está no diretório backend/")
        return
    
    # Estabelecer conexão
    conn = get_connection()
    
    try:
        # 1. Ler Excel
        df = read_excel_base_tab(excel_path)
        if df is None:
            return
        
        # 2. Analisar dados antes da migração
        analyze_data_before_migration(df)
        
        # 3. Limpar e transformar dados
        df_clean = clean_and_transform_data(df)
        if df_clean is None:
            return
        
        # 4. Inserir dados
        inserted_count = insert_financial_data(conn, df_clean, grupo_empresa_id, empresa_mapping)
        
        if inserted_count > 0:
            # 5. Validar inserção
            validate_insertion(conn, grupo_empresa_id)
            
            print(f"\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"📊 {inserted_count:,} registros da empresa TAG inseridos")
            print(f"🔗 Dados disponíveis na tabela financial_data")
            print(f"⚠️ IMPORTANTE: FKs para de_para, plano_de_contas, etc. ainda não configuradas")
            print(f"💡 Próximo passo: Migrar estruturas DRE/DFC para TAG")
            print(f"\n📈 ESTIMATIVA DE PERFORMANCE:")
            print(f"  - 37.361 registros processados")
            print(f"  - Inserção em lotes de 1.000 registros")
            print(f"  - Tempo estimado: ~2-5 minutos")
        else:
            print(f"\n❌ Nenhum registro foi inserido")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        
    finally:
        conn.close()
        print("\n🎉 PROCESSO FINALIZADO!")

if __name__ == "__main__":
    main()
