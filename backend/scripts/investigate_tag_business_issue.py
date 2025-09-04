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
        empresa_nome = "TAG Business Solutions"
        
        print(f"\n🏢 {empresa_nome} ({empresa_id})")
        
        print("\n1️⃣ VERIFICANDO CONTAS SEM DRE N2")
        print("-" * 60)
        
        # Verificar contas que não têm DRE N2
        result = conn.execute(text("""
            SELECT 
                pc.conta_pai,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NULL
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.conta_pai
            ORDER BY valor_total DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        contas_sem_dre_n2 = result.fetchall()
        print(f"📊 CONTAS SEM DRE N2 (TOP 10): {len(contas_sem_dre_n2)}")
        for row in contas_sem_dre_n2:
            print(f"   {row.conta_pai}")
            print(f"     Registros: {row.total_registros}, Valor: R$ {row.valor_total:,.2f}")
        
        print("\n2️⃣ VERIFICANDO CONTAS COM DRE N2")
        print("-" * 60)
        
        # Verificar contas que têm DRE N2
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.classificacao_dre_n2
            ORDER BY valor_total DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        contas_com_dre_n2 = result.fetchall()
        print(f"📊 CONTAS COM DRE N2 (TOP 10): {len(contas_com_dre_n2)}")
        for row in contas_com_dre_n2:
            print(f"   {row.classificacao_dre_n2}")
            print(f"     Registros: {row.total_registros}, Valor: R$ {row.valor_total:,.2f}")
        
        print("\n3️⃣ VERIFICANDO DIFERENÇA ENTRE FLUXO E VIEW")
        print("-" * 60)
        
        # Verificar diferença específica
        result = conn.execute(text("""
            WITH fluxo_completo AS (
                SELECT 
                    pc.classificacao_dre_n2,
                    SUM(fd.valor_original) as valor_fluxo
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                WHERE fd.empresa_id = :empresa_id
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND ds2.is_active = true
                AND fd.valor_original IS NOT NULL
                GROUP BY pc.classificacao_dre_n2
            ),
            view_valores AS (
                SELECT 
                    descricao,
                    valor_total as valor_view
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
                AND valor_total != 0
            )
            SELECT 
                fc.classificacao_dre_n2,
                fc.valor_fluxo,
                vv.valor_view,
                (vv.valor_view - fc.valor_fluxo) as diferenca,
                CASE 
                    WHEN fc.valor_fluxo != 0 THEN 
                        ((vv.valor_view - fc.valor_fluxo) / abs(fc.valor_fluxo)) * 100
                    ELSE 0
                END as percentual_diferenca
            FROM fluxo_completo fc
            LEFT JOIN view_valores vv ON fc.classificacao_dre_n2 = vv.descricao
            ORDER BY abs((vv.valor_view - fc.valor_fluxo)) DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        diferencas = result.fetchall()
        print(f"📊 DIFERENÇAS ENTRE FLUXO E VIEW (TOP 10):")
        for row in diferencas:
            status = "✅" if abs(row.percentual_diferenca) < 1 else "❌"
            print(f"   {status} {row.classificacao_dre_n2}")
            print(f"     Fluxo: R$ {row.valor_fluxo:,.2f}")
            print(f"     View: R$ {row.valor_view:,.2f}")
            print(f"     Diferença: R$ {row.diferenca:,.2f} ({row.percentual_diferenca:+.1f}%)")
        
        print("\n4️⃣ VERIFICANDO CONTAS PERDIDAS")
        print("-" * 60)
        
        # Verificar contas que estão no fluxo mas não na view
        result = conn.execute(text("""
            WITH fluxo_completo AS (
                SELECT 
                    pc.classificacao_dre_n2,
                    SUM(fd.valor_original) as valor_fluxo
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                WHERE fd.empresa_id = :empresa_id
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND ds2.is_active = true
                AND fd.valor_original IS NOT NULL
                GROUP BY pc.classificacao_dre_n2
            ),
            view_valores AS (
                SELECT 
                    descricao,
                    valor_total as valor_view
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
            )
            SELECT 
                fc.classificacao_dre_n2,
                fc.valor_fluxo
            FROM fluxo_completo fc
            LEFT JOIN view_valores vv ON fc.classificacao_dre_n2 = vv.descricao
            WHERE vv.descricao IS NULL
            ORDER BY fc.valor_fluxo DESC
        """), {"empresa_id": empresa_id})
        
        contas_perdidas = result.fetchall()
        print(f"📊 CONTAS PERDIDAS (no fluxo mas não na view): {len(contas_perdidas)}")
        for row in contas_perdidas:
            print(f"   {row.classificacao_dre_n2}: R$ {row.valor_fluxo:,.2f}")
        
        print("\n5️⃣ VERIFICANDO CONTAS EXTRA NA VIEW")
        print("-" * 60)
        
        # Verificar contas que estão na view mas não no fluxo
        result = conn.execute(text("""
            WITH fluxo_completo AS (
                SELECT 
                    pc.classificacao_dre_n2
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                WHERE fd.empresa_id = :empresa_id
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND ds2.is_active = true
                AND fd.valor_original IS NOT NULL
                GROUP BY pc.classificacao_dre_n2
            ),
            view_valores AS (
                SELECT 
                    descricao,
                    valor_total as valor_view
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
                AND valor_total != 0
            )
            SELECT 
                vv.descricao,
                vv.valor_view
            FROM view_valores vv
            LEFT JOIN fluxo_completo fc ON vv.descricao = fc.classificacao_dre_n2
            WHERE fc.classificacao_dre_n2 IS NULL
            ORDER BY vv.valor_view DESC
        """), {"empresa_id": empresa_id})
        
        contas_extra = result.fetchall()
        print(f"📊 CONTAS EXTRA (na view mas não no fluxo): {len(contas_extra)}")
        for row in contas_extra:
            print(f"   {row.descricao}: R$ {row.valor_view:,.2f}")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 INVESTIGAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Contas sem DRE N2 estão sendo perdidas")
        print("   2. JOIN da view pode estar falhando para algumas contas")
        print("   3. DRE_STRUCTURE_N2 pode ter contas inativas")
        print("   4. View pode ter lógica específica que não funciona para TAG Business")

if __name__ == "__main__":
    main()
