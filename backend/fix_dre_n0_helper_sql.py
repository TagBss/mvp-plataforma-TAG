#!/usr/bin/env python3
"""
Script para corrigir o SQL do DreN0Helper com a sintaxe correta
"""

def fix_dre_n0_helper_sql():
    """Corrige o SQL do DreN0Helper"""
    
    print("🔧 CORRIGINDO SQL DO DRE N0 HELPER...")
    
    try:
        # 1. Ler o arquivo atual
        file_path = "helpers_postgresql/dre/dre_n0_helper.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   📄 Arquivo lido: {file_path}")
        
        # 2. SQL correto para substituir
        old_sql = '''                CREATE OR REPLACE VIEW v_dre_n0_completo AS
                WITH dados_limpos AS (
                    -- Filtrar dados válidos da financial_data usando IDs corrigidos
                    SELECT 
                        _id,
                        _id,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                    FROM financial_data fd
                    WHERE (_id IS NOT NULL OR _id IS NOT NULL)
                    AND fd.valor_original IS NOT NULL 
                    AND fd.competencia IS NOT NULL
                ),'''
        
        new_sql = '''                CREATE OR REPLACE VIEW v_dre_n0_completo AS
                WITH dados_limpos AS (
                    -- Filtrar dados válidos da financial_data usando IDs corrigidos
                    SELECT 
                        fd.dre_n1_id,
                        fd.dre_n2_id,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                    FROM financial_data fd
                    WHERE (fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL)
                    AND fd.valor_original IS NOT NULL 
                    AND fd.competencia IS NOT NULL
                ),'''
        
        # 3. Fazer a substituição
        print("\n🔄 3. CORRIGINDO SQL PROBLEMÁTICO:")
        
        if old_sql in content:
            content = content.replace(old_sql, new_sql)
            print("   ✅ SQL corrigido")
        else:
            print("   ⚠️ SQL problemático não encontrado (pode ter sido alterado)")
        
        # 4. Verificar se a correção foi aplicada
        print("\n🔍 4. VERIFICANDO CORREÇÃO:")
        
        if '_id,' in content:
            print("   ❌ Ainda há '_id,' incorreto no SQL")
        else:
            print("   ✅ '_id,' incorreto removido")
        
        if 'fd.dre_n1_id' in content and 'fd.dre_n2_id' in content:
            print("   ✅ Colunas corretas 'fd.dre_n1_id' e 'fd.dre_n2_id' presentes")
        else:
            print("   ❌ Colunas corretas não encontradas")
        
        # 5. Salvar o arquivo corrigido
        print("\n💾 5. SALVANDO ARQUIVO CORRIGIDO:")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Arquivo salvo: {file_path}")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = fix_dre_n0_helper_sql()
        if success:
            print("\n🎯 SQL DO DRE N0 HELPER CORRIGIDO!")
        else:
            print("\n❌ ERRO AO CORRIGIR SQL!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
