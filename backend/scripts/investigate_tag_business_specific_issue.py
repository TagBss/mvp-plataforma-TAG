#!/usr/bin/env python3
"""
Script para investigar especificamente o problema da TAG Business Solutions
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 INVESTIGANDO PROBLEMA ESPECÍFICO DA TAG BUSINESS SOLUTIONS")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresa_id = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        
        print("\n1️⃣ VERIFICANDO CONTAS DRE ESPECÍFICAS")
        print("-" * 60)
        
        # Verificar contas DRE específicas
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND ds2.is_active = true
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.classificacao_dre_n2
            ORDER BY valor_total DESC
        """), {"empresa_id": empresa_id})
        
        contas_dre = result.fetchall()
        print(f"📊 CONTAS DRE ESPECÍFICAS: {len(contas_dre)}")
        for row in contas_dre:
            print(f"   {row.classificacao_dre_n2}: R$ {row.valor_total:,.2f}")
        
        print("\n2️⃣ VERIFICANDO VIEW ESPECÍFICA")
        print("-" * 60)
        
        # Verificar view específica
        result = conn.execute(text("""
            SELECT 
                descricao,
                valor_total
            FROM v_dre_n0_completo
            WHERE empresa_id = :empresa_id
            AND valor_total != 0
            ORDER BY valor_total DESC
        """), {"empresa_id": empresa_id})
        
        view_contas = result.fetchall()
        print(f"📊 VIEW ESPECÍFICA: {len(view_contas)}")
        for row in view_contas:
            print(f"   {row.descricao}: R$ {row.valor_total:,.2f}")
        
        print("\n3️⃣ COMPARANDO CONTAS INDIVIDUAIS")
        print("-" * 60)
        
        # Comparar contas individuais
        for conta_dre in contas_dre:
            classificacao = conta_dre.classificacao_dre_n2
            valor_dre = conta_dre.valor_total
            
            # Buscar na view
            result = conn.execute(text("""
                SELECT valor_total
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
                AND descricao = :classificacao
            """), {"empresa_id": empresa_id, "classificacao": classificacao})
            
            view_row = result.fetchone()
            valor_view = view_row.valor_total if view_row else 0
            
            diferenca = valor_view - valor_dre
            percentual = (diferenca / abs(valor_dre)) * 100 if valor_dre != 0 else 0
            
            status = "✅" if abs(percentual) < 1 else "❌"
            print(f"   {status} {classificacao}")
            print(f"     DRE: R$ {valor_dre:,.2f}")
            print(f"     View: R$ {valor_view:,.2f}")
            print(f"     Diferença: R$ {diferenca:,.2f} ({percentual:+.1f}%)")
        
        print("\n4️⃣ VERIFICANDO CONTAS PERDIDAS")
        print("-" * 60)
        
        # Verificar contas que estão no DRE mas não na view
        contas_dre_nomes = [row.classificacao_dre_n2 for row in contas_dre]
        view_contas_nomes = [row.descricao for row in view_contas]
        
        contas_perdidas = [nome for nome in contas_dre_nomes if nome not in view_contas_nomes]
        contas_extra = [nome for nome in view_contas_nomes if nome not in contas_dre_nomes]
        
        print(f"📊 CONTAS PERDIDAS (no DRE mas não na view): {len(contas_perdidas)}")
        for conta in contas_perdidas:
            print(f"   {conta}")
        
        print(f"\n📊 CONTAS EXTRA (na view mas não no DRE): {len(contas_extra)}")
        for conta in contas_extra:
            print(f"   {conta}")
        
        print("\n5️⃣ VERIFICANDO DRE_STRUCTURE_N2")
        print("-" * 60)
        
        # Verificar se todas as contas DRE existem no dre_structure_n2
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                ds2.description,
                ds2.is_active,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            LEFT JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.classificacao_dre_n2, ds2.description, ds2.is_active
            ORDER BY valor_total DESC
        """), {"empresa_id": empresa_id})
        
        dre_structure_check = result.fetchall()
        print(f"📊 VERIFICAÇÃO DRE_STRUCTURE_N2:")
        for row in dre_structure_check:
            status = "✅" if row.is_active else "❌"
            print(f"   {status} {row.classificacao_dre_n2}")
            print(f"     Description: {row.description}")
            print(f"     Active: {row.is_active}")
            print(f"     Valor: R$ {row.valor_total:,.2f}")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 INVESTIGAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Contas podem estar sendo perdidas no JOIN da view")
        print("   2. DRE_STRUCTURE_N2 pode ter contas inativas")
        print("   3. View pode ter lógica específica que não funciona para TAG Business")
        print("   4. Pode haver diferenças de nomenclatura entre as tabelas")

if __name__ == "__main__":
    main()
