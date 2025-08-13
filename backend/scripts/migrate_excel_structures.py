#!/usr/bin/env python3
"""
Script para migrar estruturas DFC e DRE exatamente como estão nas abas do Excel
"""
import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import (
    FinancialData, 
    DFCStructureN1, DFCStructureN2, DFCClassification,
    DREStructureN1, DREStructureN2, DREClassification
)
from helpers.structure_helper import extrair_tipo_operacao, extrair_nome_conta

def migrar_estruturas_do_excel():
    """Migra as estruturas DFC e DRE diretamente das abas do Excel"""
    
    try:
        filename = "db_bluefit - Copia.xlsx"
        
        if not os.path.exists(filename):
            print(f"❌ Arquivo {filename} não encontrado!")
            return
        
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 80)
        print("🔧 MIGRANDO ESTRUTURAS DFC E DRE DO EXCEL")
        print("=" * 80)
        
        # ===== LIMPEZA DAS TABELAS DE ESTRUTURA =====
        print("\n🧹 Limpando tabelas de estrutura existentes...")
        
        session.query(DFCClassification).delete()
        session.query(DFCStructureN2).delete()
        session.query(DFCStructureN1).delete()
        session.query(DREClassification).delete()
        session.query(DREStructureN2).delete()
        session.query(DREStructureN1).delete()
        session.commit()
        
        print("✅ Tabelas limpas com sucesso!")
        
        # ===== MIGRAÇÃO DFC =====
        print("\n📊 Migrando estruturas DFC do Excel...")
        
        # 1. Migrar DFC N1
        df_dfc_n1 = pd.read_excel(filename, sheet_name="dfc_n1")
        print(f"📋 DFC N1: {len(df_dfc_n1)} registros encontrados")
        
        for _, row in df_dfc_n1.iterrows():
            dfc_n1_id = int(row['dfc_n1_id'])
            dfc_n1_texto = str(row['dfc_n1'])
            
            nome = extrair_nome_conta(dfc_n1_texto)
            operacao = extrair_tipo_operacao(dfc_n1_texto)
            
            dfc_n1_obj = DFCStructureN1(
                dfc_n1_id=dfc_n1_id,
                name=nome,
                operation_type=operacao,
                description=f"Migrado do Excel: {dfc_n1_texto}",
                order_index=dfc_n1_id,
                is_active=True
            )
            session.add(dfc_n1_obj)
            print(f"  ✅ DFC N1 {dfc_n1_id}: {nome} ({operacao})")
        
        session.commit()
        
        # 2. Migrar DFC N2
        df_dfc_n2 = pd.read_excel(filename, sheet_name="dfc_n2")
        print(f"\n📋 DFC N2: {len(df_dfc_n2)} registros encontrados")
        
        for _, row in df_dfc_n2.iterrows():
            dfc_n2_id = int(row['dfc_n2_id'])
            dfc_n2_texto = str(row['dfc_n2'])
            dfc_n1_texto = str(row['dfc_n1'])
            
            # Encontrar dfc_n1_id correspondente
            dfc_n1_match = df_dfc_n1[df_dfc_n1['dfc_n1'] == dfc_n1_texto]
            if dfc_n1_match.empty:
                print(f"  ⚠️ DFC N1 não encontrado para: {dfc_n1_texto}")
                continue
            
            dfc_n1_id = int(dfc_n1_match.iloc[0]['dfc_n1_id'])
            
            nome = extrair_nome_conta(dfc_n2_texto)
            operacao = extrair_tipo_operacao(dfc_n2_texto)
            
            dfc_n2_obj = DFCStructureN2(
                dfc_n2_id=dfc_n2_id,
                dfc_n1_id=dfc_n1_id,
                name=nome,
                operation_type=operacao,
                description=f"Migrado do Excel: {dfc_n2_texto}",
                order_index=dfc_n2_id,
                is_active=True
            )
            session.add(dfc_n2_obj)
            print(f"  ✅ DFC N2 {dfc_n2_id}: {nome} ({operacao}) -> N1: {dfc_n1_id}")
        
        session.commit()
        
        # 3. Criar classificações DFC baseadas nos dados reais
        print(f"\n📋 Criando classificações DFC baseadas nos dados...")
        
        # Buscar classificações únicas da financial_data para cada DFC N2
        financial_data = session.query(FinancialData).filter(
            FinancialData.dfc_n1.isnot(None),
            FinancialData.dfc_n2.isnot(None),
            FinancialData.classificacao.isnot(None)
        ).all()
        
        # Criar mapeamento de nomes DFC N2 para IDs
        dfc_n2_name_to_id = {}
        for _, row in df_dfc_n2.iterrows():
            nome = extrair_nome_conta(str(row['dfc_n2']))
            dfc_n2_name_to_id[nome] = int(row['dfc_n2_id'])
        
        # Agrupar classificações por DFC N2
        classificacoes_por_dfc_n2 = {}
        for record in financial_data:
            dfc_n2_nome_dados = extrair_nome_conta(str(record.dfc_n2))
            classificacao = str(record.classificacao).strip()
            
            # Encontrar ID correspondente
            dfc_n2_id = None
            for nome_estrutura, id_estrutura in dfc_n2_name_to_id.items():
                if nome_estrutura.lower() == dfc_n2_nome_dados.lower():
                    dfc_n2_id = id_estrutura
                    break
            
            if dfc_n2_id and classificacao and classificacao != 'nan':
                if dfc_n2_id not in classificacoes_por_dfc_n2:
                    classificacoes_por_dfc_n2[dfc_n2_id] = set()
                classificacoes_por_dfc_n2[dfc_n2_id].add(classificacao)
        
        # Criar registros de classificação
        classification_id = 1
        for dfc_n2_id, classificacoes in classificacoes_por_dfc_n2.items():
            for classificacao in sorted(classificacoes):
                dfc_class_obj = DFCClassification(
                    dfc_n2_id=dfc_n2_id,
                    name=classificacao,
                    description=f"Classificação migrada dos dados: {classificacao}",
                    order_index=classification_id,
                    is_active=True
                )
                session.add(dfc_class_obj)
                classification_id += 1
        
        session.commit()
        print(f"  ✅ {classification_id - 1} classificações DFC criadas")
        
        # ===== MIGRAÇÃO DRE =====
        print("\n📊 Migrando estruturas DRE do Excel...")
        
        # 1. Migrar DRE N1
        df_dre_n1 = pd.read_excel(filename, sheet_name="dre_n1")
        print(f"📋 DRE N1: {len(df_dre_n1)} registros encontrados")
        
        for _, row in df_dre_n1.iterrows():
            dre_n1_id = int(row['dre_n1_id'])
            dre_n1_texto = str(row['dre_n1'])
            
            nome = extrair_nome_conta(dre_n1_texto)
            operacao = extrair_tipo_operacao(dre_n1_texto)
            
            dre_n1_obj = DREStructureN1(
                dre_n1_id=dre_n1_id,
                name=nome,
                operation_type=operacao,
                description=f"Migrado do Excel: {dre_n1_texto}",
                order_index=dre_n1_id,
                is_active=True
            )
            session.add(dre_n1_obj)
            print(f"  ✅ DRE N1 {dre_n1_id}: {nome} ({operacao})")
        
        session.commit()
        
        # 2. Migrar DRE N2
        df_dre_n2 = pd.read_excel(filename, sheet_name="dre_n2")
        print(f"\n📋 DRE N2: {len(df_dre_n2)} registros encontrados")
        
        for _, row in df_dre_n2.iterrows():
            dre_n2_id = int(row['dre_n2_id'])
            dre_n2_texto = str(row['dre_n2'])
            dre_n1_texto = str(row['dre_n1'])
            
            # Encontrar dre_n1_id correspondente
            dre_n1_match = df_dre_n1[df_dre_n1['dre_n1'] == dre_n1_texto]
            if dre_n1_match.empty:
                print(f"  ⚠️ DRE N1 não encontrado para: {dre_n1_texto}")
                continue
            
            dre_n1_id = int(dre_n1_match.iloc[0]['dre_n1_id'])
            
            nome = extrair_nome_conta(dre_n2_texto)
            operacao = extrair_tipo_operacao(dre_n2_texto)
            
            dre_n2_obj = DREStructureN2(
                dre_n2_id=dre_n2_id,
                dre_n1_id=dre_n1_id,
                name=nome,
                operation_type=operacao,
                description=f"Migrado do Excel: {dre_n2_texto}",
                order_index=dre_n2_id,
                is_active=True
            )
            session.add(dre_n2_obj)
            print(f"  ✅ DRE N2 {dre_n2_id}: {nome} ({operacao}) -> N1: {dre_n1_id}")
        
        session.commit()
        
        # 3. Criar classificações DRE baseadas nos dados reais
        print(f"\n📋 Criando classificações DRE baseadas nos dados...")
        
        # Buscar classificações únicas da financial_data para cada DRE N2
        financial_data_dre = session.query(FinancialData).filter(
            FinancialData.dre_n1.isnot(None),
            FinancialData.dre_n2.isnot(None),
            FinancialData.classificacao.isnot(None)
        ).all()
        
        # Criar mapeamento de nomes DRE N2 para IDs
        dre_n2_name_to_id = {}
        for _, row in df_dre_n2.iterrows():
            nome = extrair_nome_conta(str(row['dre_n2']))
            dre_n2_name_to_id[nome] = int(row['dre_n2_id'])
        
        # Agrupar classificações por DRE N2
        classificacoes_por_dre_n2 = {}
        for record in financial_data_dre:
            dre_n2_nome_dados = extrair_nome_conta(str(record.dre_n2))
            classificacao = str(record.classificacao).strip()
            
            # Encontrar ID correspondente
            dre_n2_id = None
            for nome_estrutura, id_estrutura in dre_n2_name_to_id.items():
                if nome_estrutura.lower() == dre_n2_nome_dados.lower():
                    dre_n2_id = id_estrutura
                    break
            
            if dre_n2_id and classificacao and classificacao != 'nan':
                if dre_n2_id not in classificacoes_por_dre_n2:
                    classificacoes_por_dre_n2[dre_n2_id] = set()
                classificacoes_por_dre_n2[dre_n2_id].add(classificacao)
        
        # Criar registros de classificação DRE
        classification_id = 1
        for dre_n2_id, classificacoes in classificacoes_por_dre_n2.items():
            for classificacao in sorted(classificacoes):
                dre_class_obj = DREClassification(
                    dre_n2_id=dre_n2_id,
                    name=classificacao,
                    description=f"Classificação migrada dos dados: {classificacao}",
                    order_index=classification_id,
                    is_active=True
                )
                session.add(dre_class_obj)
                classification_id += 1
        
        session.commit()
        print(f"  ✅ {classification_id - 1} classificações DRE criadas")
        
        session.close()
        
        print("\n" + "=" * 80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
        # Executar verificação final
        print("\n🔍 Executando verificação final...")
        os.system("python check_structure_tables.py")
        
    except Exception as e:
        print(f"❌ Erro geral na migração: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrar_estruturas_do_excel()
