#!/usr/bin/env python3
"""
Script robusto para reimportar TODOS os dados do Excel
Tratando corretamente valores NULL e garantindo importação completa
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys

def clean_and_import_all_data():
    print("🚀 REIMPORTAÇÃO COMPLETA E ROBUSTA")
    print("=" * 50)
    
    try:
        # 1. Ler Excel
        print("1. Carregando Excel...")
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        print(f"   ✅ {len(df)} registros carregados do Excel")
        
        # 2. Limpar dados existentes
        print("2. Limpando tabela atual...")
        with DatabaseSession() as session:
            session.execute(text("DELETE FROM financial_data"))
            session.commit()
            print("   ✅ Tabela limpa")
        
        # 3. Importar dados em lotes com tratamento robusto de NULL
        print("3. Importando dados...")
        batch_size = 100
        total_imported = 0
        total_errors = 0
        
        with DatabaseSession() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                batch_imported = 0
                
                print(f"   📦 Lote {i//batch_size + 1}: registros {i+1}-{min(i+batch_size, len(df))}")
                
                for idx, row in batch.iterrows():
                    try:
                        # Preparar valores com tratamento robusto de NULL
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
                        
                        # Função helper para tratar valores
                        def safe_value(value, default=None):
                            if pd.isna(value) or value is None:
                                return default
                            return value
                        
                        def safe_date(value):
                            if pd.isna(value) or value is None:
                                return None
                            try:
                                return value.date() if hasattr(value, 'date') else None
                            except:
                                return None
                        
                        def safe_float(value):
                            if pd.isna(value) or value is None:
                                return None
                            try:
                                return float(value)
                            except:
                                return None
                        
                        def safe_string(value):
                            if pd.isna(value) or value is None:
                                return None
                            return str(value).strip() if str(value).strip() != 'nan' else None
                        
                        values = {
                            'origem': safe_string(row['origem']),
                            'empresa': safe_string(row['empresa']),
                            'nome': safe_string(row['nome']),
                            'classificacao': safe_string(row['classificacao']),
                            'emissao': safe_date(row['emissao']),
                            'competencia': safe_date(row['competencia']),
                            'vencimento': safe_date(row['vencimento']),
                            'valor_original': safe_float(row['valor_original']),
                            'data': safe_date(row['data']),
                            'valor': safe_float(row['valor']),
                            'banco': safe_string(row['banco']),
                            'conta_corrente': safe_string(row['conta corrente']),
                            'documento': safe_string(row['documento']),
                            'observacao': safe_string(row['observação']),
                            'local': safe_string(row['local']),
                            'segmento': safe_string(row['segmento']),
                            'projeto': safe_string(row['projeto']),
                            'centro_de_resultado': safe_string(row['centro de resultado']),
                            'diretoria': safe_string(row['diretoria']),
                            'dre_n1': safe_string(row['dre_n1']),
                            'dre_n2': safe_string(row['dre_n2']),
                            'dfc_n1': safe_string(row['dfc_n1']),
                            'dfc_n2': safe_string(row['dfc_n2'])
                        }
                        
                        session.execute(insert_sql, values)
                        batch_imported += 1
                        total_imported += 1
                        
                    except Exception as e:
                        total_errors += 1
                        print(f"      ⚠️ Erro na linha {idx}: {str(e)[:100]}")
                        continue
                
                # Commit do lote
                try:
                    session.commit()
                    print(f"      ✅ {batch_imported} registros inseridos neste lote")
                except Exception as e:
                    print(f"      ❌ Erro no commit do lote: {e}")
                    session.rollback()
        
        # 4. Verificar resultado
        print("4. Verificando resultado...")
        with DatabaseSession() as session:
            result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
            final_count = result.fetchone()[0]
            
            print(f"\\n🎉 IMPORTAÇÃO CONCLUÍDA!")
            print(f"📊 Excel: {len(df)} registros")
            print(f"📊 Importados: {total_imported} registros")
            print(f"📊 Na tabela: {final_count} registros")
            print(f"⚠️ Erros: {total_errors}")
            print(f"✅ Taxa de sucesso: {(total_imported/len(df)*100):.1f}%")
            
            if final_count == len(df):
                print("🎯 SUCESSO TOTAL - Todos os registros importados!")
            elif final_count > len(df) * 0.95:
                print("✅ SUCESSO - Mais de 95% dos registros importados!")
            else:
                print("⚠️ ATENÇÃO - Menos de 95% dos registros importados!")
    
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    clean_and_import_all_data()
