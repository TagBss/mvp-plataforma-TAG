#!/usr/bin/env python3
"""
Teste para verificar se os endpoints DRE e DFC estão funcionando corretamente
após a separação dos arquivos.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint_name, url):
    """Testa um endpoint específico."""
    print(f"\n=== Testando {endpoint_name} ===")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"Erro no endpoint: {data['error']}")
            else:
                print("✅ Endpoint funcionando corretamente!")
                if "data" in data:
                    print(f"Dados retornados: {len(data['data'])} itens")
                elif "meses" in data:
                    print(f"Meses: {len(data['meses'])} | Trimestres: {len(data['trimestres'])} | Anos: {len(data['anos'])}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def main():
    """Testa todos os endpoints principais."""
    print("=== TESTE DE ENDPOINTS APÓS SEPARAÇÃO ===")
    
    # Testa endpoint raiz
    test_endpoint("Root", f"{BASE_URL}/")
    
    # Testa endpoint DRE
    test_endpoint("DRE", f"{BASE_URL}/dre")
    
    # Testa endpoint DFC
    test_endpoint("DFC", f"{BASE_URL}/dfc")
    
    # Testa outros endpoints
    test_endpoint("Receber", f"{BASE_URL}/receber")
    test_endpoint("Pagar", f"{BASE_URL}/pagar")
    test_endpoint("Movimentações", f"{BASE_URL}/movimentacoes")
    test_endpoint("Saldos Evolução", f"{BASE_URL}/saldos-evolucao")
    test_endpoint("Custos Visão Financeiro", f"{BASE_URL}/custos-visao-financeiro")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    main()
