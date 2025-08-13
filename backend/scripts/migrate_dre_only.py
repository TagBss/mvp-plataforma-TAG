#!/usr/bin/env python3
"""
Script simples para migrar apenas a estrutura DRE
"""

import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.schema_sqlalchemy import DREStructureN1, DREStructureN2, DREClassification
from helpers.structure_helper import extrair_nome_conta, extrair_tipo_operacao

def get_database_connection():
    """Criar conexão com o banco PostgreSQL"""
    try:
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/tag_financeiro')
        engine = create_engine(db_url)
        
        # Testar conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        return None

def migrate_dre_simple(engine, filename):
    """Migrar estrutura DRE de forma simplificada"""
    print("\n🔄 Migrando estrutura DRE (simplificada)...")
    
    try:
        # Carregar apenas a aba DRE simplificada
        print("  📥 Carregando aba DRE...")
        df_dre = pd.read_excel(filename, sheet_name="dre")
        
        if df_dre.empty:
            print("  ⚠️  Aba DRE está vazia")
            return False
        
        print(f"  📊 Encontradas {len(df_dre)} linhas na aba DRE")
        
        # Criar sessão
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Limpar estruturas DRE existentes
            print("  🗑️  Limpando estruturas DRE existentes...")
            session.query(DREClassification).delete()
            session.query(DREStructureN2).delete()
            session.query(DREStructureN1).delete()
            session.commit()
            
            # Migrar DRE simplificada
            print("  📊 Migrando contas DRE...")
            contas_migradas = 0
            
            for _, row in df_dre.iterrows():
                try:
                    dre_id = row.get('dre_id')
                    dre_name = str(row.get('dre', ''))
                    
                    # Verificar se os dados são válidos
                    if pd.isna(dre_id) or pd.isna(dre_name) or not str(dre_name).strip():
                        continue
                    
                    # Verificar se dre_id é um número válido
                    try:
                        dre_id_int = int(dre_id)
                        if dre_id_int <= 0 or dre_id_int > 999999:
                            print(f"    ⚠️  Pulando ID inválido: {dre_id}")
                            continue
                    except (ValueError, TypeError):
                        print(f"    ⚠️  Pulando ID não numérico: {dre_id}")
                        continue
                    
                    nome = extrair_nome_conta(dre_name)
                    tipo = extrair_tipo_operacao(dre_name)
                    
                    dre_n1 = DREStructureN1(
                        dre_n1_id=dre_id_int,
                        name=nome,
                        operation_type=tipo,
                        order_index=dre_id_int,
                        description=f"Conta DRE: {nome}"
                    )
                    session.add(dre_n1)
                    contas_migradas += 1
                    
                except Exception as e:
                    print(f"    ⚠️  Erro ao processar linha: {e}")
                    continue
            
            session.commit()
            print(f"  ✅ {contas_migradas} contas DRE migradas com sucesso")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"  ❌ Erro durante migração DRE: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"  ❌ Erro ao migrar estrutura DRE: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 MIGRAÇÃO SIMPLIFICADA DA ESTRUTURA DRE")
    print("=" * 50)
    
    # Arquivo Excel
    filename = "db_bluefit - Copia.xlsx"
    
    if not os.path.exists(filename):
        print(f"❌ Arquivo {filename} não encontrado")
        return
    
    # Conectar ao banco
    engine = get_database_connection()
    if not engine:
        return
    
    try:
        # Migrar DRE
        success = migrate_dre_simple(engine, filename)
        
        if success:
            print("\n🎉 Migração DRE concluída com sucesso!")
        else:
            print("\n❌ Migração DRE falhou")
    
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
