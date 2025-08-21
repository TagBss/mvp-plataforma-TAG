#!/usr/bin/env python3
"""
Script para corrigir o DreN0Helper removendo colunas antigas
"""

import re

def fix_dre_n0_helper():
    """Corrige o DreN0Helper removendo colunas antigas"""
    
    print("🔧 CORRIGINDO DRE N0 HELPER...")
    
    try:
        # 1. Ler o arquivo atual
        file_path = "helpers_postgresql/dre/dre_n0_helper.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   📄 Arquivo lido: {file_path}")
        
        # 2. Identificar problemas
        print("\n🔍 2. IDENTIFICANDO PROBLEMAS:")
        
        # Verificar colunas antigas
        old_columns = ['fd.dre_n2', 'fd.dre_n1']
        for col in old_columns:
            if col in content:
                print(f"   ❌ Coluna antiga encontrada: {col}")
            else:
                print(f"   ✅ Coluna antiga NÃO encontrada: {col}")
        
        # Verificar colunas corretas
        correct_columns = ['fd.dre_n1_id', 'fd.dre_n2_id']
        for col in correct_columns:
            if col in content:
                print(f"   ✅ Coluna correta encontrada: {col}")
            else:
                print(f"   ❌ Coluna correta NÃO encontrada: {col}")
        
        # 3. Corrigir o código problemático
        print("\n🔄 3. CORRIGINDO CÓDIGO PROBLEMÁTICO:")
        
        # Substituir SELECT com colunas antigas
        old_select = '''                    SELECT 
                        fd.dre_n2,
                        fd.dre_n1,
                        fd.dre_n1_id,
                        fd.dre_n2_id,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual'''
        
        new_select = '''                    SELECT 
                        fd.dre_n1_id,
                        fd.dre_n2_id,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual'''
        
        # Fazer a substituição
        if old_select in content:
            content = content.replace(old_select, new_select)
            print("   ✅ SELECT com colunas antigas corrigido")
        else:
            print("   ⚠️ SELECT com colunas antigas não encontrado")
        
        # 4. Verificar se há outros problemas
        print("\n🔍 4. VERIFICANDO OUTROS PROBLEMAS:")
        
        # Verificar se ainda há colunas antigas
        remaining_old = []
        for col in old_columns:
            if col in content:
                remaining_old.append(col)
        
        if remaining_old:
            print(f"   ❌ Ainda há colunas antigas: {remaining_old}")
        else:
            print("   ✅ Todas as colunas antigas foram removidas")
        
        # 5. Salvar o arquivo corrigido
        print("\n💾 5. SALVANDO ARQUIVO CORRIGIDO:")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Arquivo salvo: {file_path}")
        
        # 6. Verificar se a correção foi aplicada
        print("\n🔍 6. VERIFICANDO CORREÇÃO:")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            corrected_content = f.read()
        
        if 'fd.dre_n2' not in corrected_content and 'fd.dre_n1' not in corrected_content:
            print("   ✅ Colunas antigas removidas com sucesso")
        else:
            print("   ❌ Colunas antigas ainda presentes")
        
        if 'fd.dre_n1_id' in corrected_content and 'fd.dre_n2_id' in corrected_content:
            print("   ✅ Colunas corretas mantidas")
        else:
            print("   ❌ Colunas corretas não encontradas")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = fix_dre_n0_helper()
        if success:
            print("\n🎯 DRE N0 HELPER CORRIGIDO!")
        else:
            print("\n❌ ERRO AO CORRIGIR HELPER!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
