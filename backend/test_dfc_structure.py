#!/usr/bin/env python3
"""
Teste para verificar a estrutura DFC e identificar problemas de conversão
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from endpoints.dfc import carregar_estrutura_dfc, extrair_tipo_operacao, extrair_nome_conta

def test_dfc_structure():
    """Testa o carregamento da estrutura DFC"""
    filename = "backend/financial-data-roriz.xlsx"
    
    print("🔍 Testando carregamento da estrutura DFC...")
    
    try:
        # Testar carregamento da estrutura
        estrutura = carregar_estrutura_dfc(filename)
        print(f"✅ Estrutura carregada com {len(estrutura)} itens")
        
        for i, item in enumerate(estrutura[:5]):  # Mostrar apenas os primeiros 5
            print(f"  {i+1}. Nome: '{item['nome']}' | Tipo: '{item['tipo']}' | Totalizador: '{item['totalizador']}'")
        
        # Testar carregamento dos dados principais
        print("\n🔍 Testando carregamento dos dados principais...")
        df = pd.read_excel(filename, sheet_name="base")
        print(f"✅ Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"   Colunas: {list(df.columns)}")
        
        # Verificar coluna valor
        if "valor" in df.columns:
            print(f"✅ Coluna 'valor' encontrada")
            print(f"   Tipos de dados: {df['valor'].dtype}")
            print(f"   Exemplos: {df['valor'].head().tolist()}")
            
            # Testar conversão numérica
            try:
                valores_numericos = pd.to_numeric(df["valor"], errors="coerce")
                print(f"✅ Conversão numérica bem-sucedida")
                print(f"   Valores não-nulos: {valores_numericos.notna().sum()}")
                print(f"   Exemplos convertidos: {valores_numericos.dropna().head().tolist()}")
            except Exception as e:
                print(f"❌ Erro na conversão numérica: {e}")
        
        # Verificar coluna DFC_n2
        if "DFC_n2" in df.columns:
            print(f"✅ Coluna 'DFC_n2' encontrada")
            print(f"   Valores únicos: {df['DFC_n2'].nunique()}")
            print(f"   Exemplos: {df['DFC_n2'].dropna().head().tolist()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dfc_structure() 