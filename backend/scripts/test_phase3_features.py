#!/usr/bin/env python3
"""
Script para testar as funcionalidades da Fase 3
"""
import requests
import json
import time
from typing import Dict, Any

# Configurações
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_debounce():
    """Testa o sistema de debounce"""
    print("🧪 Testando sistema de debounce...")
    
    # Primeira requisição (deve ser permitida)
    response1 = requests.post(f"{BASE_URL}/dre-n0/performance/debounce?operation=test_operation&ttl=5")
    print(f"  Requisição 1: {response1.status_code} - {response1.json()}")
    
    # Segunda requisição imediata (deve ser bloqueada)
    response2 = requests.post(f"{BASE_URL}/dre-n0/performance/debounce?operation=test_operation&ttl=5")
    print(f"  Requisição 2: {response2.status_code} - {response2.json()}")
    
    # Aguardar e tentar novamente
    print("  Aguardando 6 segundos...")
    time.sleep(6)
    
    response3 = requests.post(f"{BASE_URL}/dre-n0/performance/debounce?operation=test_operation&ttl=5")
    print(f"  Requisição 3: {response3.status_code} - {response3.json()}")
    
    return response1.status_code == 200 and response2.status_code == 200 and response3.status_code == 200

def test_compression():
    """Testa o sistema de compressão"""
    print("🧪 Testando sistema de compressão...")
    
    # Dados de exemplo para compressão
    sample_data = {
        "data": [
            {
                "valores_mensais": {
                    "2025-01": 123456.789123456,
                    "2025-02": 234567.890123456,
                    "2025-03": 345678.901234567
                },
                "valores_trimestrais": {
                    "2025-Q1": 704703.580481479
                },
                "valores_anuais": {
                    "2025": 704703.580481479
                }
            }
        ],
        "meses": ["2025-01", "2025-02", "2025-03"],
        "trimestres": ["2025-Q1"],
        "anos": ["2025"]
    }
    
    response = requests.post(f"{BASE_URL}/dre-n0/performance/compress", 
                           json=sample_data, 
                           params={"compression_ratio": 0.8})
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Compressão bem-sucedida")
        print(f"  Tamanho original: {result.get('original_size', 'N/A')}")
        print(f"  Tamanho comprimido: {result.get('compressed_size', 'N/A')}")
        print(f"  Taxa de compressão: {result.get('compression_ratio', 'N/A')}")
        return True
    else:
        print(f"  ❌ Erro na compressão: {response.status_code}")
        return False

def test_performance_metrics():
    """Testa o sistema de métricas de performance"""
    print("🧪 Testando sistema de métricas...")
    
    # Primeiro, executar algumas operações para gerar métricas
    print("  Gerando métricas de teste...")
    
    # Simular operação
    response1 = requests.post(f"{BASE_URL}/dre-n0/performance/monitor?operation=test_metrics")
    print(f"  Monitoramento: {response1.status_code}")
    
    # Aguardar um pouco
    time.sleep(1)
    
    # Buscar métricas
    response2 = requests.get(f"{BASE_URL}/dre-n0/performance/metrics")
    
    if response2.status_code == 200:
        result = response2.json()
        print(f"  ✅ Métricas obtidas com sucesso")
        print(f"  Operações monitoradas: {len(result.get('metrics', {}))}")
        return True
    else:
        print(f"  ❌ Erro ao obter métricas: {response2.status_code}")
        return False

def test_query_optimization():
    """Testa o sistema de otimização de queries"""
    print("🧪 Testando sistema de otimização de queries...")
    
    response = requests.post(f"{BASE_URL}/dre-n0/performance/optimize?query_name=dre_n0_main")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Otimização bem-sucedida")
        print(f"  Query otimizada: {result.get('optimization_result', {}).get('query_name', 'N/A')}")
        print(f"  Índices encontrados: {len(result.get('optimization_result', {}).get('indexes', []))}")
        return True
    else:
        print(f"  ❌ Erro na otimização: {response.status_code}")
        return False

def test_performance_monitoring():
    """Testa o sistema de monitoramento de performance"""
    print("🧪 Testando sistema de monitoramento...")
    
    response = requests.get(f"{BASE_URL}/dre-n0/performance/monitor?operation=test_monitoring")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Monitoramento bem-sucedido")
        print(f"  Operação: {result.get('monitoring_result', {}).get('operation', 'N/A')}")
        print(f"  Tempo de execução: {result.get('monitoring_result', {}).get('execution_time', 'N/A')}")
        print(f"  Nível de performance: {result.get('monitoring_result', {}).get('performance_level', 'N/A')}")
        return True
    else:
        print(f"  ❌ Erro no monitoramento: {response.status_code}")
        return False

def test_refactored_endpoints():
    """Testa os endpoints refatorados"""
    print("🧪 Testando endpoints refatorados...")
    
    # Testar endpoint principal
    response1 = requests.get(f"{BASE_URL}/dre-n0/?page=1&page_size=10")
    print(f"  Endpoint principal: {response1.status_code}")
    
    # Testar endpoint de paginação
    response2 = requests.get(f"{BASE_URL}/dre-n0/paginated?page=1&page_size=5")
    print(f"  Endpoint paginado: {response2.status_code}")
    
    # Testar endpoint de debug
    response3 = requests.get(f"{BASE_URL}/dre-n0/debug/structure")
    print(f"  Endpoint debug: {response3.status_code}")
    
    # Testar endpoint de classificações
    response4 = requests.get(f"{BASE_URL}/dre-n0/classificacoes/(%20%2B%20)%20Faturamento")
    print(f"  Endpoint classificações: {response4.status_code}")
    
    return all(r.status_code == 200 for r in [response1, response2, response3, response4])

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DA FASE 3")
    print("=" * 50)
    
    tests = [
        ("Debounce", test_debounce),
        ("Compressão", test_compression),
        ("Métricas de Performance", test_performance_metrics),
        ("Otimização de Queries", test_query_optimization),
        ("Monitoramento de Performance", test_performance_monitoring),
        ("Endpoints Refatorados", test_refactored_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 {test_name}")
            print("-" * 30)
            success = test_func()
            results.append((test_name, success))
            print(f"  {'✅ PASSOU' if success else '❌ FALHOU'}")
        except Exception as e:
            print(f"  ❌ ERRO: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Fase 3 implementada com sucesso!")
    else:
        print("⚠️  Alguns testes falharam. Verificar implementação.")
    
    return passed == total

if __name__ == "__main__":
    main()
