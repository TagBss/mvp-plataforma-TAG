#!/usr/bin/env python3
"""
Script para recriar as tabelas de estrutura DFC e DRE baseadas nos dados reais da financial_data
"""
import sys
import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import (
    FinancialData, 
    DFCStructureN1, DFCStructureN2, DFCClassification,
    DREStructureN1, DREStructureN2, DREClassification
)

def extrair_operador_e_nome(categoria_str):
    """Extrai operador e nome limpo da categoria do Excel"""
    if not categoria_str or categoria_str == 'nan':
        return None, None
    
    categoria_str = str(categoria_str).strip()
    
    # Padrão: ( OPERADOR ) NOME
    match = re.match(r'\(\s*([=+\-+/\*])\s*\)\s*(.*)', categoria_str)
    if match:
        operador = match.group(1)
        nome_limpo = match.group(2).strip()
        return operador, nome_limpo
    else:
        # Se não tem operador, é um nome direto
        return '=', categoria_str

def recriar_estruturas():
    """Recria as tabelas de estrutura baseadas nos dados reais"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 80)
        print("🔧 RECRIANDO ESTRUTURAS DFC E DRE")
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
        
        # ===== RECRIAÇÃO DAS ESTRUTURAS DFC =====
        print("\n📊 Recriando estruturas DFC...")
        
        # Buscar valores únicos de DFC N1 dos dados
        dfc_n1_values = session.query(FinancialData.dfc_n1).distinct().all()
        dfc_n1_data = {}
        dfc_n1_id_counter = 1
        
        for dfc_n1_raw in dfc_n1_values:
            if dfc_n1_raw[0] is not None and str(dfc_n1_raw[0]).strip() != '':
                operador, nome_limpo = extrair_operador_e_nome(dfc_n1_raw[0])
                if nome_limpo:
                    dfc_n1_data[nome_limpo] = {
                        'id': dfc_n1_id_counter,
                        'operador': operador or '=',
                        'nome_original': dfc_n1_raw[0]
                    }
                    dfc_n1_id_counter += 1
        
        # Criar registros DFC N1
        for nome_limpo, data in dfc_n1_data.items():
            dfc_n1 = DFCStructureN1(
                dfc_n1_id=data['id'],
                name=nome_limpo,
                operation_type=data['operador'],
                description=f"Criado automaticamente dos dados - {data['nome_original']}",
                order_index=data['id'],
                is_active=True
            )
            session.add(dfc_n1)
        
        session.commit()
        print(f"✅ Criados {len(dfc_n1_data)} registros DFC N1")
        
        # Buscar valores únicos de DFC N2 dos dados
        dfc_n2_values = session.query(FinancialData.dfc_n2, FinancialData.dfc_n1).distinct().all()
        dfc_n2_data = {}
        dfc_n2_id_counter = 1
        
        for dfc_n2_raw, dfc_n1_raw in dfc_n2_values:
            if (dfc_n2_raw is not None and str(dfc_n2_raw).strip() != '' and
                dfc_n1_raw is not None and str(dfc_n1_raw).strip() != ''):
                
                operador_n2, nome_limpo_n2 = extrair_operador_e_nome(dfc_n2_raw)
                operador_n1, nome_limpo_n1 = extrair_operador_e_nome(dfc_n1_raw)
                
                if nome_limpo_n2 and nome_limpo_n1 and nome_limpo_n1 in dfc_n1_data:
                    key = f"{nome_limpo_n1}::{nome_limpo_n2}"
                    if key not in dfc_n2_data:
                        dfc_n2_data[key] = {
                            'id': dfc_n2_id_counter,
                            'dfc_n1_id': dfc_n1_data[nome_limpo_n1]['id'],
                            'nome': nome_limpo_n2,
                            'operador': operador_n2 or '=',
                            'nome_original': dfc_n2_raw
                        }
                        dfc_n2_id_counter += 1
        
        # Criar registros DFC N2
        for key, data in dfc_n2_data.items():
            dfc_n2 = DFCStructureN2(
                dfc_n2_id=data['id'],
                dfc_n1_id=data['dfc_n1_id'],
                name=data['nome'],
                operation_type=data['operador'],
                description=f"Criado automaticamente dos dados - {data['nome_original']}",
                order_index=data['id'],
                is_active=True
            )
            session.add(dfc_n2)
        
        session.commit()
        print(f"✅ Criados {len(dfc_n2_data)} registros DFC N2")
        
        # Criar classificações DFC baseadas nas classificações dos dados
        print("\n📋 Criando classificações DFC...")
        
        # Buscar classificações únicas por DFC N2
        classificacoes_dfc = session.query(
            FinancialData.classificacao, 
            FinancialData.dfc_n2,
            FinancialData.dfc_n1
        ).distinct().all()
        
        dfc_classifications_created = 0
        classification_id_counter = 1
        
        for classificacao_raw, dfc_n2_raw, dfc_n1_raw in classificacoes_dfc:
            if (classificacao_raw is not None and str(classificacao_raw).strip() != '' and
                dfc_n2_raw is not None and str(dfc_n2_raw).strip() != '' and
                dfc_n1_raw is not None and str(dfc_n1_raw).strip() != ''):
                
                operador_n2, nome_limpo_n2 = extrair_operador_e_nome(dfc_n2_raw)
                operador_n1, nome_limpo_n1 = extrair_operador_e_nome(dfc_n1_raw)
                
                if nome_limpo_n2 and nome_limpo_n1:
                    key = f"{nome_limpo_n1}::{nome_limpo_n2}"
                    if key in dfc_n2_data:
                        dfc_n2_id = dfc_n2_data[key]['id']
                        
                        # Verificar se a classificação já existe para este DFC N2
                        existing = session.query(DFCClassification).filter(
                            DFCClassification.dfc_n2_id == dfc_n2_id,
                            DFCClassification.name == classificacao_raw
                        ).first()
                        
                        if not existing:
                            classification = DFCClassification(
                                dfc_n2_id=dfc_n2_id,
                                name=classificacao_raw,
                                description=f"Classificação criada automaticamente dos dados",
                                order_index=classification_id_counter,
                                is_active=True
                            )
                            session.add(classification)
                            dfc_classifications_created += 1
                            classification_id_counter += 1
        
        session.commit()
        print(f"✅ Criadas {dfc_classifications_created} classificações DFC")
        
        # ===== RECRIAÇÃO DAS ESTRUTURAS DRE =====
        print("\n📊 Recriando estruturas DRE...")
        
        # Buscar valores únicos de DRE N1 dos dados
        dre_n1_values = session.query(FinancialData.dre_n1).distinct().all()
        dre_n1_data = {}
        dre_n1_id_counter = 1
        
        for dre_n1_raw in dre_n1_values:
            if dre_n1_raw[0] is not None and str(dre_n1_raw[0]).strip() != '':
                operador, nome_limpo = extrair_operador_e_nome(dre_n1_raw[0])
                if nome_limpo:
                    dre_n1_data[nome_limpo] = {
                        'id': dre_n1_id_counter,
                        'operador': operador or '=',
                        'nome_original': dre_n1_raw[0]
                    }
                    dre_n1_id_counter += 1
        
        # Criar registros DRE N1
        for nome_limpo, data in dre_n1_data.items():
            dre_n1 = DREStructureN1(
                dre_n1_id=data['id'],
                name=nome_limpo,
                operation_type=data['operador'],
                description=f"Criado automaticamente dos dados - {data['nome_original']}",
                order_index=data['id'],
                is_active=True
            )
            session.add(dre_n1)
        
        session.commit()
        print(f"✅ Criados {len(dre_n1_data)} registros DRE N1")
        
        # Buscar valores únicos de DRE N2 dos dados
        dre_n2_values = session.query(FinancialData.dre_n2, FinancialData.dre_n1).distinct().all()
        dre_n2_data = {}
        dre_n2_id_counter = 1
        
        for dre_n2_raw, dre_n1_raw in dre_n2_values:
            if (dre_n2_raw is not None and str(dre_n2_raw).strip() != '' and
                dre_n1_raw is not None and str(dre_n1_raw).strip() != ''):
                
                operador_n2, nome_limpo_n2 = extrair_operador_e_nome(dre_n2_raw)
                operador_n1, nome_limpo_n1 = extrair_operador_e_nome(dre_n1_raw)
                
                if nome_limpo_n2 and nome_limpo_n1 and nome_limpo_n1 in dre_n1_data:
                    key = f"{nome_limpo_n1}::{nome_limpo_n2}"
                    if key not in dre_n2_data:
                        dre_n2_data[key] = {
                            'id': dre_n2_id_counter,
                            'dre_n1_id': dre_n1_data[nome_limpo_n1]['id'],
                            'nome': nome_limpo_n2,
                            'operador': operador_n2 or '=',
                            'nome_original': dre_n2_raw
                        }
                        dre_n2_id_counter += 1
        
        # Criar registros DRE N2
        for key, data in dre_n2_data.items():
            dre_n2 = DREStructureN2(
                dre_n2_id=data['id'],
                dre_n1_id=data['dre_n1_id'],
                name=data['nome'],
                operation_type=data['operador'],
                description=f"Criado automaticamente dos dados - {data['nome_original']}",
                order_index=data['id'],
                is_active=True
            )
            session.add(dre_n2)
        
        session.commit()
        print(f"✅ Criados {len(dre_n2_data)} registros DRE N2")
        
        # Criar classificações DRE baseadas nas classificações dos dados
        print("\n📋 Criando classificações DRE...")
        
        # Buscar classificações únicas por DRE N2
        classificacoes_dre = session.query(
            FinancialData.classificacao, 
            FinancialData.dre_n2,
            FinancialData.dre_n1
        ).filter(
            FinancialData.dre_n1.isnot(None),
            FinancialData.dre_n2.isnot(None)
        ).distinct().all()
        
        dre_classifications_created = 0
        classification_id_counter = 1
        
        for classificacao_raw, dre_n2_raw, dre_n1_raw in classificacoes_dre:
            if (classificacao_raw is not None and str(classificacao_raw).strip() != '' and
                dre_n2_raw is not None and str(dre_n2_raw).strip() != '' and
                dre_n1_raw is not None and str(dre_n1_raw).strip() != ''):
                
                operador_n2, nome_limpo_n2 = extrair_operador_e_nome(dre_n2_raw)
                operador_n1, nome_limpo_n1 = extrair_operador_e_nome(dre_n1_raw)
                
                if nome_limpo_n2 and nome_limpo_n1:
                    key = f"{nome_limpo_n1}::{nome_limpo_n2}"
                    if key in dre_n2_data:
                        dre_n2_id = dre_n2_data[key]['id']
                        
                        # Verificar se a classificação já existe para este DRE N2
                        existing = session.query(DREClassification).filter(
                            DREClassification.dre_n2_id == dre_n2_id,
                            DREClassification.name == classificacao_raw
                        ).first()
                        
                        if not existing:
                            classification = DREClassification(
                                dre_n2_id=dre_n2_id,
                                name=classificacao_raw,
                                description=f"Classificação criada automaticamente dos dados",
                                order_index=classification_id_counter,
                                is_active=True
                            )
                            session.add(classification)
                            dre_classifications_created += 1
                            classification_id_counter += 1
        
        session.commit()
        print(f"✅ Criadas {dre_classifications_created} classificações DRE")
        
        session.close()
        
        print("\n" + "=" * 80)
        print("✅ ESTRUTURAS RECRIADAS COM SUCESSO!")
        print("=" * 80)
        
        # Executar verificação final
        print("\n🔍 Executando verificação final...")
        os.system("python check_structure_tables.py")
        
    except Exception as e:
        print(f"❌ Erro geral na recriação: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recriar_estruturas()
