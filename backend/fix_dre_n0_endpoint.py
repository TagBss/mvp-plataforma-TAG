#!/usr/bin/env python3
"""
Script para corrigir o endpoint DRE N0 e parar de recriar as views
"""

import re

def fix_dre_n0_endpoint():
    """Corrige o endpoint DRE N0 para não recriar views existentes"""
    
    print("🔧 CORRIGINDO ENDPOINT DRE N0...")
    
    try:
        # 1. Ler o arquivo atual
        file_path = "endpoints/dre_n0_postgresql.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   📄 Arquivo lido: {file_path}")
        
        # 2. Identificar o problema
        print("\n🔍 2. IDENTIFICANDO PROBLEMA:")
        
        # Verificar se há código que força recriação
        if "forçando recriação para aplicar correções" in content:
            print("   ❌ Código problemático encontrado: Força recriação das views")
        else:
            print("   ✅ Código problemático NÃO encontrado")
        
        # Verificar se há verificação de view_exists
        if "view_exists" in content:
            print("   ✅ Verificação de view_exists encontrada")
        else:
            print("   ❌ Verificação de view_exists NÃO encontrada")
        
        # 3. Corrigir o código problemático
        print("\n🔄 3. CORRIGINDO CÓDIGO PROBLEMÁTICO:")
        
        # Substituir o código que força recriação
        old_code = '''            # Verificar e criar view se necessário
            view_exists = DreN0Helper.check_view_exists(connection)
            
            if not view_exists:
                print("🏗️ View DRE N0 não existe, criando...")
                if not DreN0Helper.create_dre_n0_view(connection):
                    raise HTTPException(status_code=500, detail="Erro ao criar view DRE N0")
                print("✅ View v_dre_n0_completo criada com formato correto dos trimestres")
            else:
                print("🔄 View DRE N0 já existe, forçando recriação para aplicar correções...")
                if not DreN0Helper.create_dre_n0_view(connection):
                    raise HTTPException(status_code=500, detail="Erro ao recriar view DRE N0")
                print("✅ View v_dre_n0_completo recriada com formato correto dos trimestres")'''
        
        new_code = '''            # Verificar se a view existe (sem forçar recriação)
            view_exists = DreN0Helper.check_view_exists(connection)
            
            if not view_exists:
                print("🏗️ View DRE N0 não existe, criando...")
                if not DreN0Helper.create_dre_n0_view(connection):
                    raise HTTPException(status_code=500, detail="Erro ao criar view DRE N0")
                print("✅ View v_dre_n0_completo criada com formato correto dos trimestres")
            else:
                print("✅ View DRE N0 já existe, usando view existente")'''
        
        # Fazer a substituição
        if old_code in content:
            content = content.replace(old_code, new_code)
            print("   ✅ Código problemático substituído")
        else:
            print("   ⚠️ Código problemático não encontrado (pode ter sido alterado)")
        
        # 4. Verificar se há outros problemas similares
        print("\n🔍 4. VERIFICANDO OUTROS PROBLEMAS:")
        
        # Verificar se há outras chamadas para create_dre_n0_view
        create_calls = content.count("create_dre_n0_view")
        print(f"   📊 Total de chamadas para create_dre_n0_view: {create_calls}")
        
        # Verificar se há outras verificações problemáticas
        if "forçando recriação" in content:
            print("   ❌ Ainda há código que força recriação")
        else:
            print("   ✅ Código de recriação forçada removido")
        
        # 5. Salvar o arquivo corrigido
        print("\n💾 5. SALVANDO ARQUIVO CORRIGIDO:")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Arquivo salvo: {file_path}")
        
        # 6. Verificar se a correção foi aplicada
        print("\n🔍 6. VERIFICANDO CORREÇÃO:")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            corrected_content = f.read()
        
        if "forçando recriação para aplicar correções" not in corrected_content:
            print("   ✅ Correção aplicada com sucesso")
        else:
            print("   ❌ Correção NÃO foi aplicada")
        
        if "usando view existente" in corrected_content:
            print("   ✅ Novo código implementado")
        else:
            print("   ❌ Novo código NÃO foi implementado")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = fix_dre_n0_endpoint()
        if success:
            print("\n🎯 ENDPOINT DRE N0 CORRIGIDO!")
        else:
            print("\n❌ ERRO AO CORRIGIR ENDPOINT!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
