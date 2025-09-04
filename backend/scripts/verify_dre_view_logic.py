#!/usr/bin/env python3
"""
Script para verificar se a view v_dre_n0_completo está incluindo dados incorretos
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO LÓGICA DA VIEW V_DRE_N0_COMPLETO")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresas_tag = [
            "7c0c1321-d065-4ed2-afbf-98b2524892ac",  # TAG Projetos
            "d09c3591-3de3-4a8f-913a-2e36de84610f"   # TAG Business Solutions
        ]
        
        for empresa_id in empresas_tag:
            print(f"\n🏢 EMPRESA: {empresa_id}")
            print("=" * 60)
            
            print("\n1️⃣ VERIFICANDO DADOS QUE DEVEM IR PARA DRE")
            print("-" * 60)
            
            # Verificar dados que devem ir para DRE (têm classificacao_dre_n2)
            result = conn.execute(text("""
                SELECT 
                    pc.classificacao_dre_n2,
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                AND dp.descricao_origem IS NOT NULL
                AND pc.conta_pai IS NOT NULL
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND pc.classificacao_dre_n2::text <> ''
                GROUP BY pc.classificacao_dre_n2
                ORDER BY valor_total DESC
            """), {"empresa_id": empresa_id})
            
            dados_dre = result.fetchall()
            print(f"📊 DADOS QUE DEVEM IR PARA DRE: {len(dados_dre)}")
            for row in dados_dre:
                print(f"   {row.classificacao_dre_n2}: {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n2️⃣ VERIFICANDO DADOS QUE NÃO DEVEM IR PARA DRE")
            print("-" * 60)
            
            # Verificar dados que não devem ir para DRE (não têm classificacao_dre_n2)
            result = conn.execute(text("""
                SELECT 
                    dp.descricao_destino,
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                AND dp.descricao_origem IS NOT NULL
                AND pc.conta_pai IS NOT NULL
                AND (pc.classificacao_dre_n2 IS NULL OR pc.classificacao_dre_n2::text = '')
                GROUP BY dp.descricao_destino
                ORDER BY valor_total DESC
            """), {"empresa_id": empresa_id})
            
            dados_nao_dre = result.fetchall()
            print(f"📊 DADOS QUE NÃO DEVEM IR PARA DRE: {len(dados_nao_dre)}")
            for row in dados_nao_dre:
                print(f"   {row.descricao_destino}: {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n3️⃣ VERIFICANDO VIEW V_DRE_N0_COMPLETO")
            print("-" * 60)
            
            # Verificar o que a view está retornando
            result = conn.execute(text("""
                SELECT 
                    va.descricao,
                    COUNT(*) as total_registros,
                    SUM(va.valor_total) as valor_total
                FROM v_dre_n0_completo va
                WHERE va.empresa_id = :empresa_id
                AND va.valor_total IS NOT NULL
                AND va.descricao IS NOT NULL
                GROUP BY va.descricao
                ORDER BY valor_total DESC
            """), {"empresa_id": empresa_id})
            
            view_dre = result.fetchall()
            print(f"📊 DADOS NA VIEW V_DRE_N0_COMPLETO: {len(view_dre)}")
            for row in view_dre:
                print(f"   {row.descricao}: {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n4️⃣ COMPARANDO DADOS DRE vs VIEW")
            print("-" * 60)
            
            # Comparar dados que devem ir para DRE com o que está na view
            dados_dre_dict = {row.classificacao_dre_n2: row.valor_total for row in dados_dre}
            view_dre_dict = {row.descricao: row.valor_total for row in view_dre}
            
            print("📊 COMPARAÇÃO:")
            for classificacao in dados_dre_dict:
                valor_dre = dados_dre_dict[classificacao]
                valor_view = view_dre_dict.get(classificacao, 0)
                diferenca = valor_dre - valor_view
                
                if abs(diferenca) > 0.01:  # Tolerância para diferenças de arredondamento
                    print(f"   ❌ {classificacao}:")
                    print(f"     DRE: R$ {valor_dre:,.2f}")
                    print(f"     View: R$ {valor_view:,.2f}")
                    print(f"     Diferença: R$ {diferenca:,.2f}")
                else:
                    print(f"   ✅ {classificacao}: R$ {valor_dre:,.2f}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Se a view está correta, o problema pode estar no frontend")
        print("   2. Se a view está incorreta, precisamos corrigir a lógica")
        print("   3. Verificar se as classificações e nomes estão funcionando corretamente")

if __name__ == "__main__":
    main()
