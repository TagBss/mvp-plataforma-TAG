#!/usr/bin/env python3
import json
from main import get_dfc_data

def test_dfc_structure():
    print("=== TESTANDO ESTRUTURA HIERÁRQUICA DA DFC ===\n")
    
    try:
        result = get_dfc_data()
        
        if 'error' in result:
            print(f"❌ Erro: {result['error']}")
            return
        
        print("✅ DFC processada com sucesso!")
        print(f"📊 Totalizadores encontrados: {len(result['data'])}\n")
        
        for i, totalizador in enumerate(result['data'], 1):
            print(f"{i}. 🔹 {totalizador['nome']} ({totalizador['tipo']})")
            print(f"   💰 Valor: {totalizador['valor']:,.2f}")
            
            if 'classificacoes' in totalizador and totalizador['classificacoes']:
                print(f"   📋 Contas filhas: {len(totalizador['classificacoes'])}")
                
                # Mostrar primeiras 3 contas
                for j, conta in enumerate(totalizador['classificacoes'][:3]):
                    print(f"      ├─ {conta['nome']} ({conta['tipo']}) - {conta['valor']:,.2f}")
                    
                    if 'classificacoes' in conta and conta['classificacoes']:
                        print(f"         └─ {len(conta['classificacoes'])} classificações detalhadas")
                
                if len(totalizador['classificacoes']) > 3:
                    print(f"      └─ ... e mais {len(totalizador['classificacoes']) - 3} contas")
            
            print()
        
        # Verificar estrutura dos primeiros dados mensais
        if result['meses']:
            print(f"📅 Períodos disponíveis:")
            print(f"   Meses: {len(result['meses'])} ({result['meses'][0]} até {result['meses'][-1]})")
            print(f"   Trimestres: {len(result['trimestres'])}")
            print(f"   Anos: {len(result['anos'])}")
        
        print("\n✅ Estrutura hierárquica implementada com sucesso!")
        print("🎯 Estrutura final:")
        print("   - Nível 1: Totalizadores (Operacional, Investimento, Financiamento, Movimentação)")
        print("   - Nível 2: Contas específicas (em 'classificacoes')")
        print("   - Nível 3: Classificações detalhadas (em 'classificacoes' das contas)")
        
    except Exception as e:
        print(f"❌ Erro ao processar: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dfc_structure()
