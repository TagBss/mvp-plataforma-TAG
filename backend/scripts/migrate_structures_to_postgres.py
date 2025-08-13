#!/usr/bin/env python3
"""
Script para migrar as estruturas DFC e DRE do Excel para o PostgreSQL
"""

import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.schema_sqlalchemy import (
    Base, DFCStructureN1, DFCStructureN2, DFCClassification,
    DREStructureN1, DREStructureN2, DREClassification
)
from helpers.structure_helper import extrair_nome_conta, extrair_tipo_operacao

def get_database_connection():
    """Criar conexão com o banco PostgreSQL"""
    try:
        # Usar variáveis de ambiente ou valores padrão
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/tag_financeiro')
        engine = create_engine(db_url)
        
        # Testar conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        return None

def migrate_dfc_structure(engine, filename):
    """Migrar estrutura DFC do Excel para PostgreSQL"""
    print("\n🔄 Migrando estrutura DFC...")
    
    try:
        # Carregar estruturas do Excel
        print("  📥 Carregando abas dfc_n1 e dfc_n2...")
        
        df_n1 = pd.read_excel(filename, sheet_name="dfc_n1")
        df_n2 = pd.read_excel(filename, sheet_name="dfc_n2")
        
        if df_n1.empty or df_n2.empty:
            print("  ⚠️  Abas dfc_n1 ou dfc_n2 estão vazias")
            return False
        
        # Criar sessão
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Limpar estruturas existentes
            print("  🗑️  Limpando estruturas DFC existentes...")
            session.query(DFCClassification).delete()
            session.query(DFCStructureN2).delete()
            session.query(DFCStructureN1).delete()
            session.commit()
            
            # Migrar DFC N1 (Totalizadores principais)
            print("  📊 Migrando DFC N1...")
            for _, row in df_n1.iterrows():
                dfc_n1_id = row.get('dfc_n1_id', 0)
                dfc_n1_name = str(row.get('dfc_n1', ''))
                
                if pd.notna(dfc_n1_name) and str(dfc_n1_name).strip():
                    nome = extrair_nome_conta(dfc_n1_name)
                    tipo = extrair_tipo_operacao(dfc_n1_name)
                    
                    dfc_n1 = DFCStructureN1(
                        dfc_n1_id=dfc_n1_id,
                        name=nome,
                        operation_type=tipo,
                        order_index=dfc_n1_id,
                        description=f"Totalizador DFC N1: {nome}"
                    )
                    session.add(dfc_n1)
            
            session.commit()
            print(f"  ✅ {len(df_n1)} totalizadores DFC N1 migrados")
            
            # Migrar DFC N2 (Contas específicas)
            print("  📊 Migrando DFC N2...")
            for _, row in df_n2.iterrows():
                dfc_n2_id = row.get('dfc_n2_id', 0)
                dfc_n1_id = row.get('dfc_n1_id', 0)
                dfc_n2_name = str(row.get('dfc_n2', ''))
                
                if pd.notna(dfc_n2_name) and str(dfc_n2_name).strip():
                    nome = extrair_nome_conta(dfc_n2_name)
                    tipo = extrair_tipo_operacao(dfc_n2_name)
                    
                    # Verificar se dfc_n1_id existe, se não, usar o primeiro disponível
                    if dfc_n1_id == 0 or dfc_n1_id is None:
                        # Buscar o primeiro dfc_n1 disponível
                        first_dfc_n1 = session.query(DFCStructureN1).first()
                        if first_dfc_n1:
                            dfc_n1_id = first_dfc_n1.dfc_n1_id
                        else:
                            print(f"    ⚠️  Pulando {nome} - nenhum DFC N1 disponível")
                            continue
                    
                    dfc_n2 = DFCStructureN2(
                        dfc_n2_id=dfc_n2_id,
                        dfc_n1_id=dfc_n1_id,
                        name=nome,
                        operation_type=tipo,
                        order_index=dfc_n2_id,
                        description=f"Conta DFC N2: {nome}"
                    )
                    session.add(dfc_n2)
            
            session.commit()
            print(f"  ✅ {len(df_n2)} contas DFC N2 migradas")
            
            # Migrar classificações (extrair do campo 'classificacao' dos dados)
            print("  📊 Migrando classificações DFC...")
            df_dados = pd.read_excel(filename, sheet_name="base")
            
            if not df_dados.empty and 'classificacao' in df_dados.columns:
                classificacoes_unicas = df_dados['classificacao'].dropna().unique()
                dfc_n2_ids = df_dados['dfc_n2'].dropna().unique()
                
                for dfc_n2_name in dfc_n2_ids:
                    if pd.notna(dfc_n2_name):
                        # Encontrar o dfc_n2_id correspondente
                        dfc_n2_row = df_n2[df_n2['dfc_n2'] == dfc_n2_name]
                        if not dfc_n2_row.empty:
                            dfc_n2_id = int(dfc_n2_row.iloc[0]['dfc_n2_id'])  # Converter para int Python
                            
                            # Buscar classificações para esta conta
                            classificacoes_conta = df_dados[
                                (df_dados['dfc_n2'] == dfc_n2_name) & 
                                (df_dados['classificacao'].notna())
                            ]['classificacao'].unique()
                            
                            for i, classificacao in enumerate(classificacoes_conta):
                                if pd.notna(classificacao) and str(classificacao).strip():
                                    dfc_class = DFCClassification(
                                        dfc_n2_id=dfc_n2_id,
                                        name=str(classificacao).strip(),
                                        order_index=int(i),  # Converter para int Python
                                        description=f"Classificação: {classificacao}"
                                    )
                                    session.add(dfc_class)
                
                session.commit()
                print(f"  ✅ Classificações DFC migradas")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"  ❌ Erro durante migração DFC: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"  ❌ Erro ao migrar estrutura DFC: {e}")
        return False

def migrate_dre_structure(engine, filename):
    """Migrar estrutura DRE do Excel para PostgreSQL"""
    print("\n🔄 Migrando estrutura DRE...")
    
    try:
        # Carregar estruturas do Excel
        print("  📥 Carregando abas dre_n1, dre_n2 e dre...")
        
        df_n1 = pd.read_excel(filename, sheet_name="dre_n1")
        df_n2 = pd.read_excel(filename, sheet_name="dre_n2")
        df_simplified = pd.read_excel(filename, sheet_name="dre")
        
        if df_n1.empty and df_n2.empty and df_simplified.empty:
            print("  ⚠️  Todas as abas DRE estão vazias")
            return False
        
        # Criar sessão
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Limpar estruturas existentes
            print("  🗑️  Limpando estruturas DRE existentes...")
            session.query(DREClassification).delete()
            session.query(DREStructureN2).delete()
            session.query(DREStructureN1).delete()
            session.commit()
            
            # Migrar DRE N1 (se existir)
            if not df_n1.empty:
                print("  📊 Migrando DRE N1...")
                for _, row in df_n1.iterrows():
                    dre_n1_id = row.get('dre_n1_id', 0)
                    dre_n1_name = str(row.get('dre_n1', ''))
                    
                    if pd.notna(dre_n1_name) and str(dre_n1_name).strip():
                        nome = extrair_nome_conta(dre_n1_name)
                        tipo = extrair_tipo_operacao(dre_n1_name)
                        
                        dre_n1 = DREStructureN1(
                            dre_n1_id=dre_n1_id,
                            name=nome,
                            operation_type=tipo,
                            order_index=dre_n1_id,
                            description=f"Totalizador DRE N1: {nome}"
                        )
                        session.add(dre_n1)
                
                session.commit()
                print(f"  ✅ {len(df_n1)} totalizadores DRE N1 migrados")
            
            # Migrar DRE N2 (se existir)
            if not df_n2.empty:
                print("  📊 Migrando DRE N2...")
                for _, row in df_n2.iterrows():
                    dre_n2_id = row.get('dre_n2_id', 0)
                    dre_n1_id = row.get('dre_n1_id', 0)
                    dre_n2_name = str(row.get('dre_n2', ''))
                    
                    if pd.notna(dre_n2_name) and str(dre_n2_name).strip():
                        nome = extrair_nome_conta(dre_n2_name)
                        tipo = extrair_tipo_operacao(dre_n2_name)
                        
                        # Verificar se dre_n1_id existe, se não, usar o primeiro disponível
                        if dre_n1_id == 0 or dre_n1_id is None:
                            # Buscar o primeiro dre_n1 disponível
                            first_dre_n1 = session.query(DREStructureN1).first()
                            if first_dre_n1:
                                dre_n1_id = first_dre_n1.dre_n1_id
                            else:
                                print(f"    ⚠️  Pulando {nome} - nenhum DRE N1 disponível")
                                continue
                        
                        dre_n2 = DREStructureN2(
                            dre_n2_id=dre_n2_id,
                            dre_n1_id=dre_n1_id,
                            name=nome,
                            operation_type=tipo,
                            order_index=dre_n2_id,
                            description=f"Conta DRE N2: {nome}"
                        )
                        session.add(dre_n2)
                
                session.commit()
                print(f"  ✅ {len(df_n2)} contas DRE N2 migradas")
            
            # Migrar DRE simplificada (se existir)
            if not df_simplified.empty:
                print("  📊 Migrando DRE simplificada...")
                for _, row in df_simplified.iterrows():
                    dre_id = row.get('dre_id', 0)
                    dre_name = str(row.get('dre', ''))
                    
                    if pd.notna(dre_name) and str(dre_name).strip():
                        nome = extrair_nome_conta(dre_name)
                        tipo = extrair_tipo_operacao(dre_name)
                        
                        # Verificar se dre_id é válido
                        if pd.isna(dre_id) or dre_id is None:
                            print(f"    ⚠️  Pulando {nome} - ID inválido: {dre_id}")
                            continue
                            
                        # Criar DRE N1 se não existir
                        # Verificar se dre_id não é muito grande
                        if dre_id > 999999:  # Limite seguro para Integer
                            print(f"    ⚠️  Pulando {nome} - ID muito grande: {dre_id}")
                            continue
                            
                        dre_n1 = DREStructureN1(
                            dre_n1_id=int(dre_id),  # Converter para int Python
                            name=nome,
                            operation_type=tipo,
                            order_index=int(dre_id),  # Converter para int Python
                            description=f"Conta DRE: {nome}"
                        )
                        session.add(dre_n1)
                
                session.commit()
                print(f"  ✅ {len(df_simplified)} contas DRE migradas")
            
            # Migrar classificações DRE
            print("  📊 Migrando classificações DRE...")
            df_dados = pd.read_excel(filename, sheet_name="base")
            
            if not df_dados.empty and 'classificacao' in df_dados.columns:
                for dre_n2_name in df_dados['dre_n2'].dropna().unique():
                    if pd.notna(dre_n2_name):
                        # Buscar classificações para esta conta
                        classificacoes_conta = df_dados[
                            (df_dados['dre_n2'] == dre_n2_name) & 
                            (df_dados['classificacao'].notna())
                        ]['classificacao'].unique()
                        
                        for i, classificacao in enumerate(classificacoes_conta):
                            if pd.notna(classificacao) and str(classificacao).strip():
                                # Encontrar o dre_n2_id correspondente
                                dre_n2_row = df_n2[df_n2['dre_n2'] == dre_n2_name]
                                if not dre_n2_row.empty:
                                    dre_n2_id = int(dre_n2_row.iloc[0]['dre_n2_id'])  # Converter para int Python
                                    
                                    dre_class = DREClassification(
                                        dre_n2_id=dre_n2_id,
                                        name=str(classificacao).strip(),
                                        order_index=int(i),  # Converter para int Python
                                        description=f"Classificação: {classificacao}"
                                    )
                                    session.add(dre_class)
                
                session.commit()
                print(f"  ✅ Classificações DRE migradas")
            
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

def create_tables(engine):
    """Criar todas as tabelas no banco"""
    print("\n🏗️  Criando tabelas no banco...")
    
    try:
        Base.metadata.create_all(engine)
        print("  ✅ Tabelas criadas com sucesso")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao criar tabelas: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 MIGRAÇÃO DE ESTRUTURAS DFC E DRE PARA POSTGRESQL")
    print("=" * 60)
    
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
        # Criar tabelas
        if not create_tables(engine):
            return
        
        # Migrar estruturas
        success_dfc = migrate_dfc_structure(engine, filename)
        success_dre = migrate_dre_structure(engine, filename)
        
        if success_dfc and success_dre:
            print("\n🎉 Migração concluída com sucesso!")
            print("✅ Estruturas DFC migradas")
            print("✅ Estruturas DRE migradas")
        else:
            print("\n⚠️  Migração parcialmente concluída")
            if not success_dfc:
                print("❌ Estruturas DFC não migradas")
            if not success_dre:
                print("❌ Estruturas DRE não migradas")
    
    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
