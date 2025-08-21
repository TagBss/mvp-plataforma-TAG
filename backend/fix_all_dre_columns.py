#!/usr/bin/env python3
"""
Script para corrigir todas as referências às colunas antigas DRE em todos os arquivos
"""

import os
import re

def fix_all_dre_columns():
    """Corrige todas as referências às colunas antigas DRE"""
    
    print("🔧 CORRIGINDO TODAS AS COLUNAS DRE ANTIGAS...")
    
    # Arquivos para corrigir
    files_to_fix = [
        "helpers_postgresql/dre/dre_n0_helper.py",
        "endpoints/dre_n0_postgresql.py",
        "scripts/optimize_performance.py"
    ]
    
    total_fixed = 0
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"   ⚠️ Arquivo não encontrado: {file_path}")
            continue
            
        print(f"\n📄 Corrigindo: {file_path}")
        
        try:
            # Ler arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Contar ocorrências antes
            old_count = content.count('fd.dre_n1') + content.count('fd.dre_n2')
            print(f"   📊 Ocorrências antes: {old_count}")
            
            # Substituições necessárias
            replacements = [
                # SELECT statements
                ('fd.dre_n2,', ''),
                ('fd.dre_n1,', ''),
                ('fd.dre_n2', ''),
                ('fd.dre_n1', ''),
                
                # WHERE conditions
                ('WHERE fd.dre_n2 IS NOT NULL', 'WHERE fd.dre_n2_id IS NOT NULL'),
                ('WHERE fd.dre_n1 IS NOT NULL', 'WHERE fd.dre_n1_id IS NOT NULL'),
                ('AND fd.dre_n2::text <> \'\'', ''),
                ('AND fd.dre_n2::text <> \'nan\'', ''),
                ('AND fd.dre_n1::text <> \'\'', ''),
                ('AND fd.dre_n1::text <> \'nan\'', ''),
                
                # GROUP BY
                ('GROUP BY fd.dre_n2, fd.dre_n1, fd.competencia', 'GROUP BY fd.dre_n2_id, fd.dre_n1_id, fd.competencia'),
                ('GROUP BY fd.dre_n2, fd.dre_n1', 'GROUP BY fd.dre_n2_id, fd.dre_n1_id'),
            ]
            
            # Aplicar substituições
            for old_text, new_text in replacements:
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    print(f"      ✅ Substituído: {old_text[:30]}...")
            
            # Contar ocorrências depois
            new_count = content.count('fd.dre_n1') + content.count('fd.dre_n2')
            print(f"   📊 Ocorrências depois: {new_count}")
            
            if new_count < old_count:
                # Salvar arquivo corrigido
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   💾 Arquivo salvo")
                total_fixed += 1
            else:
                print(f"   ⚠️ Nenhuma correção aplicada")
                
        except Exception as e:
            print(f"   ❌ Erro ao corrigir {file_path}: {e}")
    
    print(f"\n🎯 CORREÇÃO CONCLUÍDA!")
    print(f"   📊 Total de arquivos corrigidos: {total_fixed}")
    
    return total_fixed

if __name__ == "__main__":
    try:
        total_fixed = fix_all_dre_columns()
        print(f"\n✅ Processo concluído! {total_fixed} arquivos corrigidos.")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
