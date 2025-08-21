#!/usr/bin/env python3
"""
Script para debugar o endpoint DRE N0 e identificar o problema
"""

import requests
import json

def debug_dre_n0_endpoint():
    """Debuga o endpoint DRE N0 para identificar o problema"""
    
    print("🔍 DEBUGANDO ENDPOINT DRE N0...")
    
    try:
        # 1. Testar endpoint principal
        print("\n📊 1. TESTANDO ENDPOINT /dre-n0/:")
        response = requests.get('http://localhost:8000/dre-n0/')
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Resposta JSON válida")
                print(f"   📊 Total de itens: {data.get('total_items', 'N/A')}")
                print(f"   📊 Sucesso: {data.get('success', 'N/A')}")
            except json.JSONDecodeError:
                print(f"   ❌ Resposta não é JSON válido")
                print(f"   📄 Conteúdo: {response.text[:200]}")
        else:
            print(f"   ❌ Erro: {response.text}")
        
        # 2. Testar endpoint de classificações
        print("\n📊 2. TESTANDO ENDPOINT /dre-n0/classificacoes/:")
        response = requests.get('http://localhost:8000/dre-n0/classificacoes/Faturamento')
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Resposta JSON válida")
                print(f"   📊 Total de classificações: {data.get('total_classificacoes', 'N/A')}")
            except json.JSONDecodeError:
                print(f"   ❌ Resposta não é JSON válido")
                print(f"   📄 Conteúdo: {response.text[:200]}")
        else:
            print(f"   ❌ Erro: {response.text}")
        
        # 3. Testar endpoint de recriação de view
        print("\n📊 3. TESTANDO ENDPOINT /dre-n0/recreate-view:")
        response = requests.post('http://localhost:8000/dre-n0/recreate-view')
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Resposta JSON válida")
                print(f"   📊 Mensagem: {data.get('message', 'N/A')}")
            except json.JSONDecodeError:
                print(f"   ❌ Resposta não é JSON válido")
                print(f"   📄 Conteúdo: {response.text[:200]}")
        else:
            print(f"   ❌ Erro: {response.text}")
        
        # 4. Testar endpoint simples
        print("\n📊 4. TESTANDO ENDPOINT /dre-n0/simples:")
        response = requests.get('http://localhost:8000/dre-n0/simples')
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Resposta JSON válida")
                print(f"   📊 Total de itens: {data.get('total_items', 'N/A')}")
            except json.JSONDecodeError:
                print(f"   ❌ Resposta não é JSON válido")
                print(f"   📄 Conteúdo: {response.text[:200]}")
        else:
            print(f"   ❌ Erro: {response.text}")
        
        # 5. Verificar se há problema com as views
        print("\n🔍 5. VERIFICANDO PROBLEMAS COM AS VIEWS:")
        
        # Testar se as views estão acessíveis
        views_to_test = [
            'v_dre_n0_completo',
            'v_dre_n0_simples', 
            'v_dre_n0_por_periodo'
        ]
        
        for view in views_to_test:
            try:
                # Testar se a view pode ser acessada via SQL
                test_response = requests.get(f'http://localhost:8000/admin/table/{view}')
                if test_response.status_code == 200:
                    print(f"   ✅ {view}: Acessível via admin")
                else:
                    print(f"   ❌ {view}: Erro ao acessar via admin - {test_response.status_code}")
            except Exception as e:
                print(f"   ❌ {view}: Erro ao testar - {e}")
        
        # 6. Verificar logs do servidor
        print("\n🔍 6. VERIFICANDO LOGS DO SERVIDOR:")
        print("   📝 Verifique os logs do servidor FastAPI para mais detalhes sobre o erro 500")
        print("   📝 O erro 'Erro ao criar view DRE N0' indica problema na criação/recriação de views")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = debug_dre_n0_endpoint()
        if success:
            print("\n🎯 DEBUG CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO DEBUG!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
