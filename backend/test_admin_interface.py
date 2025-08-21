#!/usr/bin/env python3
"""
Script para testar a interface admin diretamente
"""

import requests
import re

def test_admin_interface():
    """Testa a interface admin diretamente"""
    
    print("🌐 TESTANDO INTERFACE ADMIN DIRETAMENTE...")
    
    try:
        # 1. Testar página principal do admin
        print("\n📊 1. TESTANDO /admin/database:")
        response = requests.get('http://localhost:8000/admin/database')
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"   📄 Tamanho do HTML: {len(content)} caracteres")
            
            # 2. Verificar se as views DRE N0 aparecem no HTML
            print("\n🔍 2. VERIFICANDO VIEWS DRE N0 NO HTML:")
            dre_views = ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']
            
            for view in dre_views:
                if view in content:
                    print(f"   ✅ {view}: ENCONTRADA no HTML")
                else:
                    print(f"   ❌ {view}: NÃO encontrada no HTML")
            
            # 3. Verificar contadores no HTML
            print("\n🧮 3. VERIFICANDO CONTADORES NO HTML:")
            
            # Buscar por padrões de contagem
            tables_pattern = r'Total de tabelas:\s*(\d+)'
            views_pattern = r'Total de views:\s*(\d+)'
            
            tables_match = re.search(tables_pattern, content)
            views_match = re.search(views_pattern, content)
            
            if tables_match:
                tables_count = int(tables_match.group(1))
                print(f"   📊 Contador de tabelas no HTML: {tables_count}")
            else:
                print(f"   ❌ Contador de tabelas NÃO encontrado no HTML")
            
            if views_match:
                views_count = int(views_match.group(1))
                print(f"   📊 Contador de views no HTML: {views_count}")
            else:
                print(f"   ❌ Contador de views NÃO encontrado no HTML")
            
            # 4. Verificar se há algum problema na renderização
            print("\n🔍 4. VERIFICANDO PROBLEMAS DE RENDERIZAÇÃO:")
            
            # Verificar se há erros no HTML
            if 'error' in content.lower():
                print("   ⚠️ Possível erro encontrado no HTML")
            
            # Verificar se há JavaScript que pode estar interferindo
            if '<script' in content:
                print("   📜 JavaScript encontrado no HTML")
            
            # Verificar se há CSS que pode estar escondendo elementos
            if 'display: none' in content or 'visibility: hidden' in content:
                print("   🎨 CSS pode estar escondendo elementos")
            
            # 5. Verificar estrutura do HTML
            print("\n🔍 5. VERIFICANDO ESTRUTURA DO HTML:")
            
            # Verificar se há elementos de tabela
            table_elements = content.count('<div class="table-card">')
            print(f"   📋 Elementos table-card encontrados: {table_elements}")
            
            # Verificar se há elementos de view
            view_elements = content.count('👁️')
            print(f"   📊 Elementos de view (👁️) encontrados: {view_elements}")
            
            # Verificar se há elementos de tabela
            table_elements_icon = content.count('📋')
            print(f"   📋 Elementos de tabela (📋) encontrados: {table_elements_icon}")
            
            # 6. Verificar se há problema com o footer
            print("\n🔍 6. VERIFICANDO FOOTER DO HTML:")
            
            # Buscar pelo footer onde estão os contadores
            footer_pattern = r'Total de tabelas.*?Total de views.*?Atualizado em'
            footer_match = re.search(footer_pattern, content, re.DOTALL)
            
            if footer_match:
                footer_content = footer_match.group(0)
                print(f"   ✅ Footer encontrado: {footer_content.strip()}")
            else:
                print(f"   ❌ Footer NÃO encontrado")
            
            # 7. Verificar se há problema com a lógica de renderização
            print("\n🔍 7. VERIFICANDO LÓGICA DE RENDERIZAÇÃO:")
            
            # Verificar se há loop de renderização
            if 'for item in table_info:' in content:
                print("   ✅ Loop de renderização encontrado no HTML")
            else:
                print("   ❌ Loop de renderização NÃO encontrado no HTML")
            
            # Verificar se há variáveis sendo usadas
            if 'table_info' in content:
                print("   ✅ Variável table_info encontrada no HTML")
            else:
                print("   ❌ Variável table_info NÃO encontrada no HTML")
            
        else:
            print(f"   ❌ Erro: {response.text[:200]}")
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_admin_interface()
        if success:
            print("\n🎯 TESTE CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO TESTE!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
