#!/usr/bin/env python3
"""
Script para verificar o estado das tabelas de estrutura DFC e DRE
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import DFCStructureN1, DFCStructureN2, DFCClassification, DREStructureN1, DREStructureN2, DREClassification

def verificar_tabelas_estrutura():
    """Verifica o estado atual das tabelas de estrutura"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 80)
        print("🔍 VERIFICAÇÃO DAS TABELAS DE ESTRUTURA")
        print("=" * 80)
        
        # Verificar se as tabelas existem
        inspector = engine.dialect.get_table_names(engine.connect())
        tabelas_estrutura = [
            'dfc_structure_n1', 'dfc_structure_n2', 'dfc_classifications',
            'dre_structure_n1', 'dre_structure_n2', 'dre_classifications'
        ]
        
        print("\n📋 EXISTÊNCIA DAS TABELAS:")
        for tabela in tabelas_estrutura:
            existe = tabela in inspector
            status = "✅" if existe else "❌"
            print(f"  {status} {tabela}")
        
        # Verificar contagem de registros
        print("\n📊 CONTAGEM DE REGISTROS:")
        
        try:
            count_dfc_n1 = session.query(DFCStructureN1).count()
            print(f"  📈 DFC N1: {count_dfc_n1} registros")
        except Exception as e:
            print(f"  ❌ DFC N1: Erro - {str(e)}")
        
        try:
            count_dfc_n2 = session.query(DFCStructureN2).count()
            print(f"  📈 DFC N2: {count_dfc_n2} registros")
        except Exception as e:
            print(f"  ❌ DFC N2: Erro - {str(e)}")
        
        try:
            count_dfc_class = session.query(DFCClassification).count()
            print(f"  📈 DFC Classifications: {count_dfc_class} registros")
        except Exception as e:
            print(f"  ❌ DFC Classifications: Erro - {str(e)}")
        
        try:
            count_dre_n1 = session.query(DREStructureN1).count()
            print(f"  📈 DRE N1: {count_dre_n1} registros")
        except Exception as e:
            print(f"  ❌ DRE N1: Erro - {str(e)}")
        
        try:
            count_dre_n2 = session.query(DREStructureN2).count()
            print(f"  📈 DRE N2: {count_dre_n2} registros")
        except Exception as e:
            print(f"  ❌ DRE N2: Erro - {str(e)}")
        
        try:
            count_dre_class = session.query(DREClassification).count()
            print(f"  📈 DRE Classifications: {count_dre_class} registros")
        except Exception as e:
            print(f"  ❌ DRE Classifications: Erro - {str(e)}")
        
        # Verificar alguns exemplos de DFC N1
        print("\n📖 EXEMPLOS DFC N1:")
        try:
            dfc_n1_examples = session.query(DFCStructureN1).limit(5).all()
            for item in dfc_n1_examples:
                print(f"  📌 ID: {item.dfc_n1_id} | Nome: {item.name} | Tipo: {item.operation_type}")
        except Exception as e:
            print(f"  ❌ Erro ao buscar exemplos DFC N1: {str(e)}")
        
        # Verificar alguns exemplos de DRE N1
        print("\n📖 EXEMPLOS DRE N1:")
        try:
            dre_n1_examples = session.query(DREStructureN1).limit(5).all()
            for item in dre_n1_examples:
                print(f"  📌 ID: {item.dre_n1_id} | Nome: {item.name} | Tipo: {item.operation_type}")
        except Exception as e:
            print(f"  ❌ Erro ao buscar exemplos DRE N1: {str(e)}")
        
        # Verificar relacionamentos
        print("\n🔗 VERIFICAÇÃO DE RELACIONAMENTOS:")
        try:
            # Verificar se há DFC N2 relacionados aos DFC N1
            dfc_n1_with_children = session.query(DFCStructureN1).join(DFCStructureN2).limit(3).all()
            print(f"  📈 DFC N1 com filhos N2: {len(dfc_n1_with_children)} encontrados")
            
            for parent in dfc_n1_with_children:
                children_count = session.query(DFCStructureN2).filter(
                    DFCStructureN2.dfc_n1_id == parent.dfc_n1_id
                ).count()
                print(f"    📌 {parent.name} tem {children_count} filhos N2")
        except Exception as e:
            print(f"  ❌ Erro ao verificar relacionamentos DFC: {str(e)}")
        
        try:
            # Verificar se há DRE N2 relacionados aos DRE N1
            dre_n1_with_children = session.query(DREStructureN1).join(DREStructureN2).limit(3).all()
            print(f"  📈 DRE N1 com filhos N2: {len(dre_n1_with_children)} encontrados")
            
            for parent in dre_n1_with_children:
                children_count = session.query(DREStructureN2).filter(
                    DREStructureN2.dre_n1_id == parent.dre_n1_id
                ).count()
                print(f"    📌 {parent.name} tem {children_count} filhos N2")
        except Exception as e:
            print(f"  ❌ Erro ao verificar relacionamentos DRE: {str(e)}")
        
        session.close()
        
        print("\n" + "=" * 80)
        print("✅ VERIFICAÇÃO CONCLUÍDA")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro geral na verificação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_tabelas_estrutura()
