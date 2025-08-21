#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_admin_queries():
    """Corrige todas as queries do admin que usam colunas removidas"""
    
    print("🔍 CORRIGINDO QUERIES DO ADMIN...")
    
    # Ler o arquivo
    admin_file = 'endpoints/database_admin.py'
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"   📄 Arquivo lido: {len(content)} caracteres")
    
    # Substituições necessárias
    replacements = [
        # Views de teste - remover completamente pois usam colunas que não existem
        ('CREATE OR REPLACE VIEW v_teste_simples AS\n            SELECT \n                dre_n2,\n                COUNT(*) as total_registros,\n                SUM(valor_original) as valor_total\n            FROM financial_data \n            WHERE dre_n2 IS NOT NULL \n            AND dre_n2 != \'\' \n            AND dre_n2 != \'nan\'\n            GROUP BY dre_n2\n            LIMIT 10;', 
         '-- View de teste removida pois usava colunas removidas'),
        
        # Sample data queries
        ('SELECT dre_n2, valor_original, competencia', 
         'SELECT classificacao, valor_original, competencia'),
        
        ('WHERE dre_n2 IS NOT NULL \n            AND dre_n2 != \'\' \n            AND dre_n2 != \'nan\'',
         'WHERE classificacao IS NOT NULL \n            AND classificacao != \'\' \n            AND classificacao != \'nan\''),
        
        # Variáveis
        ('dre_n2 = row[0]', 'classificacao = row[0]'),
        ('for dre_n2, valor, competencia in sample_data:', 
         'for classificacao, valor, competencia in sample_data:'),
        ('{dre_n2}', '{classificacao}'),
        ('{dre_n2 if dre_n2 else \'N/A\'}', '{classificacao if classificacao else \'N/A\'}'),
        
        # Lista de colunas órfãs
        ('\'dfc_n1\', \'dfc_n2\', \'origem\'', '\'origem\''),
        
        # CSS e JavaScript
        ('th:has-text("dfc_n1"), th:has-text("dfc_n2")', 'th:has-text("dfc_n1_id"), th:has-text("dfc_n2_id")'),
        ('elif col in [\'dfc_n1\', \'dfc_n2\']:', 'elif col in [\'dfc_n1_id\', \'dfc_n2_id\']:'),
        ('elif col_name in [\'dfc_n1\', \'dfc_n2\']:', 'elif col_name in [\'dfc_n1_id\', \'dfc_n2_id\']:'),
    ]
    
    # Aplicar substituições
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"   ✅ Substituição aplicada: {old[:50]}...")
        else:
            print(f"   ⚠️ Não encontrado: {old[:50]}...")
    
    # Escrever arquivo corrigido
    with open(admin_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   ✅ Arquivo corrigido salvo: {len(content)} caracteres")
    print("   🎯 Admin queries corrigidas com sucesso!")

if __name__ == "__main__":
    fix_admin_queries()
