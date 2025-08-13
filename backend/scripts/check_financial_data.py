#!/usr/bin/env python3
"""
Script para verificar os dados da tabela financial_data e identificar as estruturas DFC/DRE
"""
import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import FinancialData

def verificar_dados_financial():
    """Verifica os dados da tabela financial_data"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 80)
        print("🔍 VERIFICAÇÃO DOS DADOS FINANCIAL_DATA")
        print("=" * 80)
        
        # Contagem total
        total_count = session.query(FinancialData).count()
        print(f"📊 Total de registros: {total_count}")
        
        # Verificar estruturas DFC disponíveis nos dados
        print("\n📈 ESTRUTURAS DFC NOS DADOS:")
        
        # DFC N1 únicos
        dfc_n1_values = session.query(FinancialData.dfc_n1).distinct().all()
        dfc_n1_unique = [v[0] for v in dfc_n1_values if v[0] is not None and str(v[0]).strip() != '']
        print(f"  🏷️ DFC N1 únicos: {len(dfc_n1_unique)}")
        for i, dfc_n1 in enumerate(dfc_n1_unique[:10]):  # Mostrar primeiros 10
            print(f"    {i+1:2d}. {dfc_n1}")
        if len(dfc_n1_unique) > 10:
            print(f"    ... e mais {len(dfc_n1_unique) - 10} valores")
        
        # DFC N2 únicos
        dfc_n2_values = session.query(FinancialData.dfc_n2).distinct().all()
        dfc_n2_unique = [v[0] for v in dfc_n2_values if v[0] is not None and str(v[0]).strip() != '']
        print(f"\n  🏷️ DFC N2 únicos: {len(dfc_n2_unique)}")
        for i, dfc_n2 in enumerate(dfc_n2_unique[:10]):  # Mostrar primeiros 10
            print(f"    {i+1:2d}. {dfc_n2}")
        if len(dfc_n2_unique) > 10:
            print(f"    ... e mais {len(dfc_n2_unique) - 10} valores")
        
        # Verificar estruturas DRE disponíveis nos dados
        print("\n📈 ESTRUTURAS DRE NOS DADOS:")
        
        # DRE N1 únicos
        dre_n1_values = session.query(FinancialData.dre_n1).distinct().all()
        dre_n1_unique = [v[0] for v in dre_n1_values if v[0] is not None and str(v[0]).strip() != '']
        print(f"  🏷️ DRE N1 únicos: {len(dre_n1_unique)}")
        for i, dre_n1 in enumerate(dre_n1_unique[:10]):  # Mostrar primeiros 10
            print(f"    {i+1:2d}. {dre_n1}")
        if len(dre_n1_unique) > 10:
            print(f"    ... e mais {len(dre_n1_unique) - 10} valores")
        
        # DRE N2 únicos
        dre_n2_values = session.query(FinancialData.dre_n2).distinct().all()
        dre_n2_unique = [v[0] for v in dre_n2_values if v[0] is not None and str(v[0]).strip() != '']
        print(f"\n  🏷️ DRE N2 únicos: {len(dre_n2_unique)}")
        for i, dre_n2 in enumerate(dre_n2_unique[:10]):  # Mostrar primeiros 10
            print(f"    {i+1:2d}. {dre_n2}")
        if len(dre_n2_unique) > 10:
            print(f"    ... e mais {len(dre_n2_unique) - 10} valores")
        
        # Verificar classificações únicas
        print("\n📈 CLASSIFICAÇÕES NOS DADOS:")
        classificacao_values = session.query(FinancialData.classificacao).distinct().all()
        classificacao_unique = [v[0] for v in classificacao_values if v[0] is not None and str(v[0]).strip() != '']
        print(f"  🏷️ Classificações únicas: {len(classificacao_unique)}")
        for i, classificacao in enumerate(classificacao_unique[:15]):  # Mostrar primeiros 15
            print(f"    {i+1:2d}. {classificacao}")
        if len(classificacao_unique) > 15:
            print(f"    ... e mais {len(classificacao_unique) - 15} valores")
        
        # Verificar alguns exemplos de registros
        print("\n📖 EXEMPLOS DE REGISTROS:")
        examples = session.query(FinancialData).limit(5).all()
        for i, record in enumerate(examples, 1):
            print(f"  📌 Registro {i}:")
            print(f"     Nome: {record.nome}")
            print(f"     DFC N1: {record.dfc_n1}")
            print(f"     DFC N2: {record.dfc_n2}")
            print(f"     DRE N1: {record.dre_n1}")
            print(f"     DRE N2: {record.dre_n2}")
            print(f"     Classificação: {record.classificacao}")
            print(f"     Valor: {record.valor}")
            print()
        
        session.close()
        
        print("=" * 80)
        print("✅ VERIFICAÇÃO DOS DADOS CONCLUÍDA")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro geral na verificação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_dados_financial()
