#!/usr/bin/env python3
"""
Script simples para recriar e popular a tabela do zero
"""

import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from sqlalchemy import text
import sys

def main():
    print("🚀 RECRIAÇÃO SIMPLES DA TABELA")
    print("=" * 40)
    
    try:
        # 1. Ler Excel
        print("1. Lendo Excel...")
        df = pd.read_excel('db_bluefit - Copia.xlsx', sheet_name='base')
        print(f"   ✅ {len(df)} registros lidos")
        print(f"   📋 Colunas: {list(df.columns)}")
        
        # 2. Conectar ao banco
        print("\\n2. Conectando ao banco...")
        with DatabaseSession() as session:
            
            # 3. Recriar tabela
            print("3. Recriando tabela...")
            session.execute(text("DROP TABLE IF EXISTS financial_data"))
            
            create_sql = """
            CREATE TABLE financial_data (
                id SERIAL PRIMARY KEY,
                origem VARCHAR(50),
                empresa VARCHAR(255),
                nome VARCHAR(255),
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
                dfc_n2 VARCHAR(255)
            )
            """
            session.execute(text(create_sql))
            session.commit()
            print("   ✅ Tabela recriada")
            
            # 4. Inserir dados básicos primeiro
            print("4. Inserindo dados...")
            inserted = 0
            
            for index, row in df.iterrows():
                try:
                    # Inserir apenas campos essenciais primeiro
                    insert_sql = text("""
                        INSERT INTO financial_data (
                            origem, empresa, nome, classificacao, 
                            emissao, competencia, vencimento, 
                            valor_original, data, valor, 
                            dre_n1, dre_n2, dfc_n1, dfc_n2
                        ) VALUES (
                            :origem, :empresa, :nome, :classificacao,
                            :emissao, :competencia, :vencimento,
                            :valor_original, :data, :valor,
                            :dre_n1, :dre_n2, :dfc_n1, :dfc_n2
                        )
                    """)
                    
                    # Preparar valores
                    values = {}
                    values['origem'] = str(row['origem']) if pd.notna(row['origem']) else None
                    values['empresa'] = str(row['empresa']) if pd.notna(row['empresa']) else None
                    values['nome'] = str(row['nome']) if pd.notna(row['nome']) else None
                    values['classificacao'] = str(row['classificacao']) if pd.notna(row['classificacao']) else None
                    
                    # Datas
                    values['emissao'] = row['emissao'].date() if pd.notna(row['emissao']) else None
                    values['competencia'] = row['competencia'].date() if pd.notna(row['competencia']) else None
                    values['vencimento'] = row['vencimento'].date() if pd.notna(row['vencimento']) else None
                    values['data'] = row['data'].date() if pd.notna(row['data']) else None
                    
                    # Valores
                    values['valor_original'] = float(row['valor_original']) if pd.notna(row['valor_original']) else 0.0
                    values['valor'] = float(row['valor']) if pd.notna(row['valor']) else 0.0
                    
                    # Categorias
                    values['dre_n1'] = str(row['dre_n1']) if pd.notna(row['dre_n1']) else None
                    values['dre_n2'] = str(row['dre_n2']) if pd.notna(row['dre_n2']) else None
                    values['dfc_n1'] = str(row['dfc_n1']) if pd.notna(row['dfc_n1']) else None
                    values['dfc_n2'] = str(row['dfc_n2']) if pd.notna(row['dfc_n2']) else None
                    
                    session.execute(insert_sql, values)
                    inserted += 1
                    
                    if inserted % 500 == 0:
                        session.commit()
                        print(f"   📦 {inserted} registros inseridos...")
                        
                except Exception as e:
                    print(f"   ⚠️ Erro na linha {index}: {e}")
                    continue
            
            session.commit()
            print(f"   ✅ Total inserido: {inserted} registros")
            
            # 5. Verificar resultado
            result = session.execute(text("SELECT COUNT(*) FROM financial_data"))
            final_count = result.fetchone()[0]
            
            print(f"\\n🎉 CONCLUÍDO!")
            print(f"📊 Registros na tabela: {final_count}")
            print(f"📋 Esperado do Excel: {len(df)}")
            print(f"✅ Status: {'SUCESSO' if final_count == len(df) else 'VERIFICAR'}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
