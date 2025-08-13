#!/usr/bin/env python3
"""
Script para comparar os dados dos endpoints DFC Excel e DFC PostgreSQL
"""

import requests
import json
import pandas as pd
from datetime import datetime

def get_dfc_excel():
    """Buscar dados do endpoint DFC Excel"""
    try:
        response = requests.get("http://localhost:8000/dfc", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro no endpoint Excel: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao acessar endpoint Excel: {e}")
        return None

def get_dfc_postgresql():
    """Buscar dados do endpoint DFC PostgreSQL"""
    try:
        response = requests.get("http://localhost:8000/financial-data/dfc", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro no endpoint PostgreSQL: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao acessar endpoint PostgreSQL: {e}")
        return None

def compare_periods(dfc_excel, dfc_postgresql):
    """Comparar períodos disponíveis"""
    print("\n📅 COMPARAÇÃO DE PERÍODOS:")
    print("=" * 50)
    
    # Meses
    meses_excel = set(dfc_excel.get('meses', []))
    meses_postgresql = set(dfc_postgresql.get('meses', []))
    
    print(f"📊 MESES:")
    print(f"  Excel: {len(meses_excel)} meses")
    print(f"  PostgreSQL: {len(meses_postgresql)} meses")
    
    meses_diferentes = meses_excel.symmetric_difference(meses_postgresql)
    if meses_diferentes:
        print(f"  ⚠️  Diferenças: {sorted(meses_diferentes)}")
    else:
        print("  ✅ Meses idênticos")
    
    # Trimestres
    trimestres_excel = set(dfc_excel.get('trimestres', []))
    trimestres_postgresql = set(dfc_postgresql.get('trimestres', []))
    
    print(f"\n📊 TRIMESTRES:")
    print(f"  Excel: {len(trimestres_excel)} trimestres")
    print(f"  PostgreSQL: {len(trimestres_postgresql)} trimestres")
    
    trimestres_diferentes = trimestres_excel.symmetric_difference(trimestres_postgresql)
    if trimestres_diferentes:
        print(f"  ⚠️  Diferenças: {sorted(trimestres_diferentes)}")
    else:
        print("  ✅ Trimestres idênticos")
    
    # Anos
    anos_excel = set(str(ano) for ano in dfc_excel.get('anos', []))
    anos_postgresql = set(dfc_postgresql.get('anos', []))
    
    print(f"\n📊 ANOS:")
    print(f"  Excel: {len(anos_excel)} anos")
    print(f"  PostgreSQL: {len(anos_postgresql)} anos")
    
    anos_diferentes = anos_excel.symmetric_difference(anos_postgresql)
    if anos_diferentes:
        print(f"  ⚠️  Diferenças: {sorted(anos_diferentes)}")
    else:
        print("  ✅ Anos idênticos")

def compare_structure(dfc_excel, dfc_postgresql):
    """Comparar estrutura dos dados"""
    print("\n🏗️  COMPARAÇÃO DE ESTRUTURA:")
    print("=" * 50)
    
    data_excel = dfc_excel.get('data', [])
    data_postgresql = dfc_postgresql.get('data', [])
    
    print(f"📊 ESTRUTURA:")
    print(f"  Excel: {len(data_excel)} itens principais")
    print(f"  PostgreSQL: {len(data_postgresql)} itens principais")
    
    # Verificar itens principais
    nomes_excel = [item.get('nome', '') for item in data_excel]
    nomes_postgresql = [item.get('nome', '') for item in data_postgresql]
    
    print(f"\n📋 ITENS PRINCIPAIS:")
    for i, nome in enumerate(nomes_excel):
        print(f"  {i+1}. Excel: {nome}")
    
    for i, nome in enumerate(nomes_postgresql):
        print(f"  {i+1}. PostgreSQL: {nome}")
    
    # Verificar se há classificações
    classificacoes_excel = []
    for item in data_excel:
        if 'classificacoes' in item:
            classificacoes_excel.extend([c.get('nome', '') for c in item.get('classificacoes', [])])
    
    classificacoes_postgresql = []
    for item in data_postgresql:
        if 'classificacoes' in item:
            classificacoes_postgresql.extend([c.get('nome', '') for c in item.get('classificacoes', [])])
    
    print(f"\n📊 CLASSIFICAÇÕES:")
    print(f"  Excel: {len(classificacoes_excel)} classificações")
    print(f"  PostgreSQL: {len(classificacoes_postgresql)} classificações")
    
    if classificacoes_excel and classificacoes_postgresql:
        print(f"  Primeiras 5 Excel: {classificacoes_excel[:5]}")
        print(f"  Primeiras 5 PostgreSQL: {classificacoes_postgresql[:5]}")

def compare_values(dfc_excel, dfc_postgresql):
    """Comparar valores dos dados"""
    print("\n💰 COMPARAÇÃO DE VALORES:")
    print("=" * 50)
    
    # Comparar valores totais
    data_excel = dfc_excel.get('data', [])
    data_postgresql = dfc_postgresql.get('data', [])
    
    # Encontrar item de movimentações
    mov_excel = next((item for item in data_excel if item.get('nome') == 'Movimentações'), None)
    mov_postgresql = next((item for item in data_postgresql if item.get('nome') == 'Movimentações'), None)
    
    if mov_excel and mov_postgresql:
        print(f"📊 MOVIMENTAÇÕES TOTAIS:")
        print(f"  Excel: {mov_excel.get('valor', 0):,.2f}")
        print(f"  PostgreSQL: {mov_postgresql.get('valor', 0):,.2f}")
        
        diff = abs(mov_excel.get('valor', 0) - mov_postgresql.get('valor', 0))
        if diff > 0.01:
            print(f"  ⚠️  Diferença: {diff:,.2f}")
        else:
            print("  ✅ Valores idênticos")
    
    # Comparar valores por mês (primeiros 3 meses)
    if mov_excel and mov_postgresql:
        meses_comparacao = sorted(dfc_excel.get('meses', []))[:3]
        print(f"\n📊 VALORES POR MÊS (primeiros 3):")
        
        for mes in meses_comparacao:
            valor_excel = mov_excel.get('valores_mensais', {}).get(mes, 0)
            valor_postgresql = mov_postgresql.get('valores_mensais', {}).get(mes, 0)
            
            print(f"  {mes}:")
            print(f"    Excel: {valor_excel:,.2f}")
            print(f"    PostgreSQL: {valor_postgresql:,.2f}")
            
            diff = abs(valor_excel - valor_postgresql)
            if diff > 0.01:
                print(f"    ⚠️  Diferença: {diff:,.2f}")
            else:
                print(f"    ✅ Valores idênticos")

def main():
    """Função principal"""
    print("🔍 COMPARAÇÃO DOS ENDPOINTS DFC")
    print("=" * 60)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Buscar dados dos endpoints
    print("\n📥 Buscando dados do endpoint Excel...")
    dfc_excel = get_dfc_excel()
    
    print("📥 Buscando dados do endpoint PostgreSQL...")
    dfc_postgresql = get_dfc_postgresql()
    
    if not dfc_excel or not dfc_postgresql:
        print("❌ Não foi possível obter dados de um ou ambos os endpoints")
        return
    
    print("✅ Dados obtidos com sucesso!")
    
    # Fazer comparações
    compare_periods(dfc_excel, dfc_postgresql)
    compare_structure(dfc_excel, dfc_postgresql)
    compare_values(dfc_excel, dfc_postgresql)
    
    print(f"\n🏁 Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
