#!/usr/bin/env python3
"""
Script para SUBSTITUIR completamente a tabela financial_data
pela estrutura da aba "base" do Excel
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys
from datetime import datetime

def backup_old_table():
    """Fazer backup da tabela atual"""
    print("1. 💾 FAZENDO BACKUP DA TABELA ATUAL...")
    
    try:
        with DatabaseSession() as session:
            # Verificar se já existe backup
            session.execute(text("DROP TABLE IF EXISTS financial_data_backup_old"))
            
            # Criar backup
            session.execute(text("CREATE TABLE financial_data_backup_old AS SELECT * FROM financial_data"))
            session.commit()
            
            # Verificar backup
            result = session.execute(text("SELECT COUNT(*) FROM financial_data_backup_old"))
            backup_count = result.fetchone()[0]
            print(f"   ✅ Backup criado: {backup_count} registros salvos em 'financial_data_backup_old'")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Erro no backup: {e}")
        return False

def create_new_table_structure():
    """Criar nova estrutura baseada no Excel"""
    print("\\n2. 🏗️  CRIANDO NOVA ESTRUTURA DA TABELA...")
    
    try:
        with DatabaseSession() as session:
            # Excluir tabela atual
            session.execute(text("DROP TABLE IF EXISTS financial_data"))
            print("   🗑️  Tabela antiga excluída")
            
            # Criar nova tabela com estrutura exata do Excel
            create_sql = """
            CREATE TABLE financial_data (
                id SERIAL PRIMARY KEY,
                origem VARCHAR(50),
                empresa VARCHAR(255),
                nome VARCHAR(500),
                classificacao VARCHAR(255),
                emissao DATE,
                competencia DATE,
                vencimento DATE,
                valor_original DECIMAL(15,2),
                data DATE,
                valor DECIMAL(15,2),
                banco VARCHAR(255),
                conta_corrente VARCHAR(100),
                documento VARCHAR(100),
                observacao TEXT,
                local VARCHAR(100),
                segmento VARCHAR(100),
                projeto VARCHAR(100),
                centro_de_resultado VARCHAR(100),
                diretoria VARCHAR(100),
                dre_n1 VARCHAR(255),
                dre_n2 VARCHAR(255),
                dfc_n1 VARCHAR(255),
                dfc_n2 VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            session.execute(text(create_sql))
            session.commit()
            print("   ✅ Nova tabela criada com estrutura do Excel")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Erro ao criar tabela: {e}")
        return False

def import_excel_data():
    """Importar todos os dados da aba base do Excel"""
    print("\\n3. 📥 IMPORTANDO DADOS DA ABA 'BASE' DO EXCEL...")
    
    try:
        # Ler Excel
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        print(f"   📊 Lidos {len(df)} registros do Excel")
        print(f"   📋 Colunas disponíveis: {list(df.columns)}")
        
        with DatabaseSession() as session:
            inserted_count = 0
            error_count = 0
            batch_size = 100
            
            print(f"   🔄 Iniciando importação em lotes de {batch_size} registros...")
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                batch_num = i // batch_size + 1
                print(f"      📦 Processando lote {batch_num}/{(len(df) + batch_size - 1) // batch_size}...")
                
                for index, row in batch.iterrows():
                    try:
                        # Preparar dados para inserção
                        values = {
                            'origem': str(row['origem']) if pd.notna(row['origem']) else None,
                            'empresa': str(row['empresa']) if pd.notna(row['empresa']) else None,
                            'nome': str(row['nome']) if pd.notna(row['nome']) else None,
                            'classificacao': str(row['classificacao']) if pd.notna(row['classificacao']) else None,
                            'emissao': row['emissao'].date() if pd.notna(row['emissao']) else None,
                            'competencia': row['competencia'].date() if pd.notna(row['competencia']) else None,
                            'vencimento': row['vencimento'].date() if pd.notna(row['vencimento']) else None,
                            'valor_original': float(row['valor_original']) if pd.notna(row['valor_original']) else 0.0,
                            'data': row['data'].date() if pd.notna(row['data']) else None,
                            'valor': float(row['valor']) if pd.notna(row['valor']) else 0.0,
                            'banco': str(row['banco']) if pd.notna(row['banco']) else None,
                            'conta_corrente': str(row.get('conta corrente', '')) if pd.notna(row.get('conta corrente')) else None,
                            'documento': str(row.get('documento', '')) if pd.notna(row.get('documento')) else None,
                            'observacao': str(row.get('observação', '')) if pd.notna(row.get('observação')) else None,
                            'local': str(row.get('local', '')) if pd.notna(row.get('local')) else None,
                            'segmento': str(row.get('segmento', '')) if pd.notna(row.get('segmento')) else None,
                            'projeto': str(row.get('projeto', '')) if pd.notna(row.get('projeto')) else None,
                            'centro_de_resultado': str(row.get('centro de resultado', '')) if pd.notna(row.get('centro de resultado')) else None,
                            'diretoria': str(row.get('diretoria', '')) if pd.notna(row.get('diretoria')) else None,
                            'dre_n1': str(row['dre_n1']) if pd.notna(row['dre_n1']) else None,
                            'dre_n2': str(row['dre_n2']) if pd.notna(row['dre_n2']) else None,
                            'dfc_n1': str(row['dfc_n1']) if pd.notna(row['dfc_n1']) else None,
                            'dfc_n2': str(row['dfc_n2']) if pd.notna(row['dfc_n2']) else None
                        }
                        
                        # SQL de inserção
                        insert_sql = text("""
                            INSERT INTO financial_data (
                                origem, empresa, nome, classificacao, emissao, competencia, vencimento,
                                valor_original, data, valor, banco, conta_corrente, documento, observacao,
                                local, segmento, projeto, centro_de_resultado, diretoria,
                                dre_n1, dre_n2, dfc_n1, dfc_n2
                            ) VALUES (
                                :origem, :empresa, :nome, :classificacao, :emissao, :competencia, :vencimento,
                                :valor_original, :data, :valor, :banco, :conta_corrente, :documento, :observacao,
                                :local, :segmento, :projeto, :centro_de_resultado, :diretoria,
                                :dre_n1, :dre_n2, :dfc_n1, :dfc_n2
                            )
                        """)
                        
                        session.execute(insert_sql, values)
                        inserted_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"         ⚠️ Erro na linha {index}: {str(e)[:100]}...")
                        continue
                
                # Commit do lote
                session.commit()
                print(f"         ✅ Lote {batch_num} processado: {inserted_count} inseridos, {error_count} erros")
            
            print(f"   ✅ IMPORTAÇÃO CONCLUÍDA!")
            print(f"      📊 Total inserido: {inserted_count}")
            print(f"      ⚠️ Total de erros: {error_count}")
            print(f"      📈 Taxa de sucesso: {(inserted_count/(inserted_count+error_count)*100):.1f}%")
            
            return inserted_count
            
    except Exception as e:
        print(f"   ❌ Erro na importação: {e}")
        return 0

def verify_final_result():
    """Verificar resultado final"""
    print("\\n4. 🔍 VERIFICANDO RESULTADO FINAL...")
    
    try:
        with DatabaseSession() as session:
            # Contar registros
            result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
            total_count = result.fetchone()[0]
            
            # Verificar estrutura
            result = session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'financial_data'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"   📊 Total de registros: {total_count}")
            print(f"   📋 Total de colunas: {len(columns)}")
            
            print(f"\\n   📋 Estrutura da tabela:")
            for i, (col_name, data_type) in enumerate(columns, 1):
                print(f"      {i:2d}. {col_name:<25} | {data_type}")
            
            # Verificar amostra de dados DFC e DRE
            if total_count > 0:
                print(f"\\n   📊 Amostra de dados para DFC:")
                result = session.execute(text("""
                    SELECT dfc_n1, dfc_n2, valor, nome 
                    FROM financial_data 
                    WHERE dfc_n1 IS NOT NULL 
                    LIMIT 3
                """))
                for i, (n1, n2, valor, nome) in enumerate(result.fetchall(), 1):
                    print(f"      {i}. DFC N1: {n1[:40]} | N2: {n2[:40]} | Valor: {valor} | Nome: {nome[:30]}")
                
                print(f"\\n   📊 Amostra de dados para DRE:")
                result = session.execute(text("""
                    SELECT dre_n1, dre_n2, valor, nome 
                    FROM financial_data 
                    WHERE dre_n1 IS NOT NULL 
                    LIMIT 3
                """))
                for i, (n1, n2, valor, nome) in enumerate(result.fetchall(), 1):
                    print(f"      {i}. DRE N1: {n1[:40]} | N2: {n2[:40]} | Valor: {valor} | Nome: {nome[:30]}")
            
            return total_count
            
    except Exception as e:
        print(f"   ❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal"""
    print("🚀 SUBSTITUIÇÃO COMPLETA DA TABELA FINANCIAL_DATA")
    print("=" * 70)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\\n⚠️  ATENÇÃO: Esta operação irá:")
    print("   • Fazer backup da tabela atual")
    print("   • Excluir a tabela financial_data atual")
    print("   • Criar nova tabela com estrutura da aba 'base' do Excel")
    print("   • Importar TODOS os dados do Excel")
    print("   • A nova tabela servirá tanto para DFC quanto DRE")
    print("=" * 70)
    
    try:
        # 1. Backup
        if not backup_old_table():
            print("❌ Falha no backup. Operação cancelada.")
            sys.exit(1)
        
        # 2. Criar nova estrutura
        if not create_new_table_structure():
            print("❌ Falha na criação da nova estrutura. Operação cancelada.")
            sys.exit(1)
        
        # 3. Importar dados
        imported_count = import_excel_data()
        if imported_count == 0:
            print("❌ Falha na importação dos dados.")
            sys.exit(1)
        
        # 4. Verificar resultado
        final_count = verify_final_result()
        
        print("\\n" + "=" * 70)
        print("🎉 SUBSTITUIÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Registros importados: {imported_count}")
        print(f"📋 Registros na nova tabela: {final_count}")
        print(f"✅ Status: {'PERFEITO' if imported_count == final_count else 'VERIFICAR DIFERENÇAS'}")
        print("\\n🔗 A nova tabela está pronta para ser usada pelos endpoints:")
        print("   • DFC: /financial-data/dfc")
        print("   • DRE: /financial-data/dre")
        print("=" * 70)
        
    except Exception as e:
        print(f"\\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
