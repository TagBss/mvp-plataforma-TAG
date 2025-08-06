#!/usr/bin/env python3
"""
Verificação específica dos cálculos
"""

import requests
import json

def verificar_calculos():
    """Verifica se os cálculos estão corretos"""
    
    print("🔍 Verificando cálculos específicos...")
    
    try:
        # Testar DFC
        print("\n📊 Verificando DFC...")
        response = requests.get("http://localhost:8000/dfc")
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estrutura
            if len(data.get('data', [])) >= 3:
                saldo_inicial = data['data'][0]
                movimentacoes = data['data'][1]
                saldo_final = data['data'][2]
                
                print(f"✅ Estrutura correta: Saldo Inicial, Movimentações, Saldo Final")
                
                # Verificar se saldo final = saldo inicial + movimentações
                saldo_inicial_valor = saldo_inicial.get('valor', 0)
                movimentacoes_valor = movimentacoes.get('valor', 0)
                saldo_final_valor = saldo_final.get('valor', 0)
                
                print(f"   Saldo Inicial: {saldo_inicial_valor}")
                print(f"   Movimentações: {movimentacoes_valor}")
                print(f"   Saldo Final: {saldo_final_valor}")
                
                # Verificar cálculo
                calculado = saldo_inicial_valor + movimentacoes_valor
                if abs(calculado - saldo_final_valor) < 0.01:
                    print(f"✅ Cálculo correto: {saldo_inicial_valor} + {movimentacoes_valor} = {calculado}")
                else:
                    print(f"❌ Erro no cálculo: {saldo_inicial_valor} + {movimentacoes_valor} ≠ {saldo_final_valor}")
                
                # Verificar totalizadores
                if movimentacoes.get('classificacoes'):
                    totalizadores = movimentacoes['classificacoes']
                    print(f"   Totalizadores encontrados: {len(totalizadores)}")
                    
                    # Verificar se a soma dos totalizadores = movimentações
                    soma_totalizadores = sum(t.get('valor', 0) for t in totalizadores)
                    if abs(soma_totalizadores - movimentacoes_valor) < 0.01:
                        print(f"✅ Soma dos totalizadores correta: {soma_totalizadores}")
                    else:
                        print(f"❌ Erro na soma dos totalizadores: {soma_totalizadores} ≠ {movimentacoes_valor}")
                    
                    # Mostrar valores dos totalizadores
                    for totalizador in totalizadores:
                        nome = totalizador.get('nome', '')
                        valor = totalizador.get('valor', 0)
                        print(f"     - {nome}: {valor}")
        
        # Testar DRE
        print("\n📊 Verificando DRE...")
        response = requests.get("http://localhost:8000/dre")
        if response.status_code == 200:
            data = response.json()
            
            if data.get('data'):
                print(f"✅ DRE: {len(data['data'])} itens")
                
                # Verificar se há valores negativos (esperado para despesas)
                for item in data['data']:
                    nome = item.get('nome', '')
                    valor = item.get('valor', 0)
                    if valor < 0:
                        print(f"   ✅ {nome}: {valor} (negativo - esperado para despesas)")
                    else:
                        print(f"   📊 {nome}: {valor}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_calculos() 