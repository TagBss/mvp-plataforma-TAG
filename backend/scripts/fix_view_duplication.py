#!/usr/bin/env python3
"""
Script para corrigir a duplicação de valores na view v_dre_n0_completo
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 CORRIGINDO DUPLICAÇÃO NA VIEW V_DRE_N0_COMPLETO")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO PROBLEMA DE DUPLICAÇÃO")
        print("-" * 60)
        
        # Verificar se há duplicação
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                COUNT(DISTINCT fd.id) as registros_unicos,
                COUNT(*) as registros_totais,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND fd.valor_original IS NOT NULL
            AND dp.descricao_origem IS NOT NULL
            AND pc.conta_pai IS NOT NULL
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND pc.classificacao_dre_n2::text <> ''
            GROUP BY pc.classificacao_dre_n2
            HAVING COUNT(DISTINCT fd.id) <> COUNT(*)
            ORDER BY valor_total DESC
            LIMIT 5
        """))
        
        duplicacoes = result.fetchall()
        print(f"📊 CLASSIFICAÇÕES COM DUPLICAÇÃO: {len(duplicacoes)}")
        for row in duplicacoes:
            print(f"   {row.classificacao_dre_n2}:")
            print(f"     Registros únicos: {row.registros_unicos}")
            print(f"     Registros totais: {row.registros_totais}")
            print(f"     Valor total: R$ {row.valor_total:,.2f}")
        
        print("\n2️⃣ VERIFICANDO CAUSA DA DUPLICAÇÃO")
        print("-" * 60)
        
        # Verificar se há múltiplos de_para para a mesma classificacao
        result = conn.execute(text("""
            SELECT 
                fd.classificacao,
                COUNT(DISTINCT dp.id) as de_para_count,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            WHERE fd.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND fd.valor_original IS NOT NULL
            AND dp.descricao_origem IS NOT NULL
            GROUP BY fd.classificacao
            HAVING COUNT(DISTINCT dp.id) > 1
            ORDER BY valor_total DESC
            LIMIT 5
        """))
        
        multiplos_de_para = result.fetchall()
        print(f"📊 CLASSIFICAÇÕES COM MÚLTIPLOS DE_PARA: {len(multiplos_de_para)}")
        for row in multiplos_de_para:
            print(f"   {row.classificacao}:")
            print(f"     De_para count: {row.de_para_count}")
            print(f"     Total registros: {row.total_registros}")
            print(f"     Valor total: R$ {row.valor_total:,.2f}")
        
        print("\n3️⃣ VERIFICANDO MÚLTIPLOS PLANOS_DE_CONTAS")
        print("-" * 60)
        
        # Verificar se há múltiplos planos_de_contas para o mesmo de_para
        result = conn.execute(text("""
            SELECT 
                dp.descricao_destino,
                COUNT(DISTINCT pc.id) as plano_count,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND fd.valor_original IS NOT NULL
            AND dp.descricao_origem IS NOT NULL
            AND pc.conta_pai IS NOT NULL
            GROUP BY dp.descricao_destino
            HAVING COUNT(DISTINCT pc.id) > 1
            ORDER BY valor_total DESC
            LIMIT 5
        """))
        
        multiplos_planos = result.fetchall()
        print(f"📊 DE_PARA COM MÚLTIPLOS PLANOS: {len(multiplos_planos)}")
        for row in multiplos_planos:
            print(f"   {row.descricao_destino}:")
            print(f"     Plano count: {row.plano_count}")
            print(f"     Total registros: {row.total_registros}")
            print(f"     Valor total: R$ {row.valor_total:,.2f}")
        
        print("\n4️⃣ CORRIGINDO DUPLICAÇÕES")
        print("-" * 60)
        
        if duplicacoes or multiplos_de_para or multiplos_planos:
            print("🔧 PROBLEMAS DE DUPLICAÇÃO ENCONTRADOS!")
            print("   • Múltiplos de_para para a mesma classificacao")
            print("   • Múltiplos planos_de_contas para o mesmo de_para")
            print("   • Resultado: Valores duplicados na view")
            
            print("\n💡 SOLUÇÕES:")
            print("   1. Remover de_para duplicados")
            print("   2. Consolidar planos_de_contas duplicados")
            print("   3. Recriar a view com joins corretos")
        else:
            print("✅ NENHUM PROBLEMA DE DUPLICAÇÃO ENCONTRADO!")
            print("   • O problema pode estar na lógica da view")
            print("   • Verificar se há joins incorretos")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 ANÁLISE CONCLUÍDA!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Se há duplicações, corrigir os dados")
        print("   2. Se não há duplicações, corrigir a view")
        print("   3. Testar no frontend após correção")

if __name__ == "__main__":
    main()
