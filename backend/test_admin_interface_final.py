#!/usr/bin/env python3
"""
Script final para testar a interface admin e identificar o problema de renderização
"""

import requests
import re

def test_admin_interface_final():
    """Testa a interface admin e identifica o problema de renderização"""
    
    print("🌐 TESTE FINAL DA INTERFACE ADMIN...")
    
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
            
            # 4. Verificar estrutura do HTML
            print("\n🔍 4. VERIFICANDO ESTRUTURA DO HTML:")
            
            # Verificar se há elementos de tabela
            table_elements = content.count('<div class="table-card">')
            print(f"   📋 Elementos table-card encontrados: {table_elements}")
            
            # Verificar se há elementos de view
            view_elements = content.count('👁️')
            print(f"   📊 Elementos de view (👁️) encontrados: {view_elements}")
            
            # Verificar se há elementos de tabela
            table_elements_icon = content.count('📋')
            print(f"   📋 Elementos de tabela (📋) encontrados: {table_elements_icon}")
            
            # 5. Verificar se há problema com o footer
            print("\n🔍 5. VERIFICANDO FOOTER DO HTML:")
            
            # Buscar pelo footer onde estão os contadores
            footer_pattern = r'Total de tabelas.*?Total de views.*?Atualizado em'
            footer_match = re.search(footer_pattern, content, re.DOTALL)
            
            if footer_match:
                footer_content = footer_match.group(0)
                print(f"   ✅ Footer encontrado: {footer_content.strip()}")
            else:
                print(f"   ❌ Footer NÃO encontrado")
            
            # 6. Verificar se há problema com a lógica de renderização
            print("\n🔍 6. VERIFICANDO LÓGICA DE RENDERIZAÇÃO:")
            
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
            
            # 7. Verificar se há problema com o cache
            print("\n🔍 7. VERIFICANDO PROBLEMAS DE CACHE:")
            
            # Verificar se há headers de cache
            cache_headers = response.headers.get('Cache-Control', 'N/A')
            print(f"   📊 Cache-Control: {cache_headers}")
            
            # Verificar se há ETag
            etag = response.headers.get('ETag', 'N/A')
            print(f"   📊 ETag: {etag}")
            
            # 8. Verificar se há problema com JavaScript
            print("\n🔍 8. VERIFICANDO JAVASCRIPT:")
            
            # Verificar se há JavaScript que pode estar interferindo
            if '<script' in content:
                print("   📜 JavaScript encontrado no HTML")
                
                # Contar scripts
                script_count = content.count('<script')
                print(f"      📊 Total de scripts: {script_count}")
                
                # Verificar se há JavaScript que pode estar escondendo elementos
                if 'display: none' in content or 'visibility: hidden' in content:
                    print("      ⚠️ CSS pode estar escondendo elementos")
            else:
                print("   📜 Nenhum JavaScript encontrado no HTML")
            
            # 9. Verificar se há problema com CSS
            print("\n🔍 9. VERIFICANDO CSS:")
            
            # Verificar se há CSS inline
            if '<style' in content:
                print("   🎨 CSS inline encontrado no HTML")
                
                # Verificar se há CSS que pode estar escondendo elementos
                if 'display: none' in content:
                    print("      ⚠️ CSS com 'display: none' encontrado")
                if 'visibility: hidden' in content:
                    print("      ⚠️ CSS com 'visibility: hidden' encontrado")
                if 'opacity: 0' in content:
                    print("      ⚠️ CSS com 'opacity: 0' encontrado")
            else:
                print("   🎨 Nenhum CSS inline encontrado no HTML")
            
            # 10. Verificar se há problema com o conteúdo
            print("\n🔍 10. VERIFICANDO CONTEÚDO:")
            
            # Verificar se há algum erro no HTML
            if 'error' in content.lower():
                print("   ⚠️ Possível erro encontrado no HTML")
            
            # Verificar se há algum problema com caracteres especiais
            if '\\u' in content or '\\x' in content:
                print("   ⚠️ Possível problema com caracteres especiais")
            
            # 11. Verificar se há problema com a codificação
            print("\n🔍 11. VERIFICANDO CODIFICAÇÃO:")
            
            # Verificar encoding
            print(f"   📊 Encoding da resposta: {response.encoding}")
            
            # Verificar se há caracteres corrompidos
            if '' in content:
                print("   ⚠️ Caracteres corrompidos encontrados no HTML")
            
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
        success = test_admin_interface_final()
        if success:
            print("\n🎯 TESTE FINAL CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO TESTE FINAL!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
