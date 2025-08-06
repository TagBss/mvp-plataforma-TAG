#!/usr/bin/env python3
"""
Teste para comparar cálculos entre backup e código atual
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
import requests
import json

def test_calculos():
    """Testa os cálculos dos endpoints"""
    
    print("🔍 Testando cálculos dos endpoints...")
    
    try:
        # Testar endpoint DFC
        print("\n📊 Testando endpoint DFC...")
        response_dfc = requests.get("http://localhost:8000/dfc")
        if response_dfc.status_code == 200:
            data_dfc = response_dfc.json()
            print(f"✅ DFC: {len(data_dfc.get('data', []))} itens")
            
            # Verificar valores de saldo inicial
            if data_dfc.get('data'):
                saldo_inicial = data_dfc['data'][0]
                print(f"   Saldo inicial - valor total: {saldo_inicial.get('valor')}")
                print(f"   Saldo inicial - valores mensais: {list(saldo_inicial.get('valores_mensais', {}).values())[:3]}")
                
                # Verificar movimentações
                if len(data_dfc['data']) > 1:
                    movimentacoes = data_dfc['data'][1]
                    print(f"   Movimentações - valor total: {movimentacoes.get('valor')}")
                    print(f"   Movimentações - valores mensais: {list(movimentacoes.get('valores_mensais', {}).values())[:3]}")
                    
                    # Verificar totalizadores
                    if movimentacoes.get('classificacoes'):
                        print(f"   Totalizadores encontrados: {len(movimentacoes['classificacoes'])}")
                        for totalizador in movimentacoes['classificacoes'][:3]:
                            print(f"     - {totalizador.get('nome')}: {totalizador.get('valor')}")
        else:
            print(f"❌ Erro no DFC: {response_dfc.status_code}")
        
        # Testar endpoint DRE
        print("\n📊 Testando endpoint DRE...")
        response_dre = requests.get("http://localhost:8000/dre")
        if response_dre.status_code == 200:
            data_dre = response_dre.json()
            print(f"✅ DRE: {len(data_dre.get('data', []))} itens")
            
            # Verificar valores
            if data_dre.get('data'):
                for item in data_dre['data'][:3]:
                    print(f"   {item.get('nome')}: {item.get('valor')}")
        else:
            print(f"❌ Erro no DRE: {response_dre.status_code}")
        
        # Testar dados específicos
        print("\n🔍 Testando dados específicos...")
        
        # Carregar dados do Excel para verificação
        df = pd.read_excel("financial-data-roriz.xlsx")
        print(f"   Dados carregados: {len(df)} linhas")
        
        # Verificar valores por período
        if 'data' in df.columns and 'valor' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors="coerce")
            df['mes_ano'] = df['data'].dt.to_period("M").astype(str)
            
            # Separar realizado e orçamento
            df_real = df[df['origem'] != 'ORC'].copy()
            df_orc = df[df['origem'] == 'ORC'].copy()
            
            print(f"   Dados realizados: {len(df_real)} linhas")
            print(f"   Dados orçamentários: {len(df_orc)} linhas")
            
            # Verificar valores por mês
            if 'DFC_n2' in df.columns:
                valores_por_mes = df_real.groupby(['mes_ano', 'DFC_n2'])['valor'].sum()
                print(f"   Valores únicos por mês/conta: {len(valores_por_mes)}")
                
                # Mostrar alguns exemplos
                print("   Exemplos de valores:")
                for (mes, conta), valor in list(valores_por_mes.items())[:5]:
                    print(f"     {mes} - {conta}: {valor}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_calculos() 