#!/usr/bin/env python3
"""
Script para corrigir as 2 contas específicas que não têm DRE N2
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 CORRIGINDO CONTAS ESPECÍFICAS SEM DRE N2")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresa_id = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        
        print("\n1️⃣ IDENTIFICANDO CONTAS ESPECÍFICAS")
        print("-" * 60)
        
        # Identificar contas específicas sem DRE N2
        contas_problema = [
            ("[ 4.01.002 ] Movimentação entre contas", "( + / - ) Receitas / Despesas não recorrentes"),
            ("[ 3.01.001 ] Empréstimos Bancários", "( + / - ) Receitas / Despesas não recorrentes")
        ]
        
        for conta_origem, conta_destino in contas_problema:
            print(f"\n🔄 Corrigindo: {conta_origem} → {conta_destino}")
            
            # Verificar se a conta existe no plano_de_contas
            result = conn.execute(text("""
                SELECT 
                    conta_pai,
                    classificacao_dre_n2,
                    COUNT(*) as total_registros
                FROM plano_de_contas
                WHERE empresa_id = :empresa_id
                AND conta_pai = :conta_origem
                GROUP BY conta_pai, classificacao_dre_n2
            """), {"empresa_id": empresa_id, "conta_origem": conta_origem})
            
            antes = result.fetchall()
            print(f"   ANTES: {len(antes)} registros")
            for row in antes:
                print(f"     {row.conta_pai}: {row.classificacao_dre_n2} ({row.total_registros} registros)")
            
            # Verificar se a conta destino existe no dre_structure_n2
            result = conn.execute(text("""
                SELECT id, description
                FROM dre_structure_n2
                WHERE description = :conta_destino
                AND is_active = true
            """), {"conta_destino": conta_destino})
            
            dre_n2_exists = result.fetchone()
            if dre_n2_exists:
                print(f"   ✅ Conta destino encontrada: {dre_n2_exists.description}")
                
                # Atualizar plano_de_contas
                result = conn.execute(text("""
                    UPDATE plano_de_contas
                    SET classificacao_dre_n2 = :conta_destino
                    WHERE conta_pai = :conta_origem
                    AND empresa_id = :empresa_id
                """), {
                    "conta_destino": conta_destino,
                    "conta_origem": conta_origem,
                    "empresa_id": empresa_id
                })
                
                rows_updated = result.rowcount
                print(f"   ✅ {rows_updated} registros atualizados")
                
                # Verificar depois do update
                result = conn.execute(text("""
                    SELECT 
                        conta_pai,
                        classificacao_dre_n2,
                        COUNT(*) as total_registros
                    FROM plano_de_contas
                    WHERE empresa_id = :empresa_id
                    AND conta_pai = :conta_origem
                    GROUP BY conta_pai, classificacao_dre_n2
                """), {"empresa_id": empresa_id, "conta_origem": conta_origem})
                
                depois = result.fetchall()
                print(f"   DEPOIS: {len(depois)} registros")
                for row in depois:
                    print(f"     {row.conta_pai}: {row.classificacao_dre_n2} ({row.total_registros} registros)")
            else:
                print(f"   ❌ Conta destino não encontrada: {conta_destino}")
        
        print("\n2️⃣ VERIFICANDO RESULTADO FINAL")
        print("-" * 60)
        
        # Verificar se ainda há contas sem DRE N2
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
        """), {"empresa_id": empresa_id})
        
        contas_sem_dre_n2 = result.fetchall()
        print(f"📊 CONTAS SEM DRE N2 APÓS CORREÇÃO: {len(contas_sem_dre_n2)}")
        for row in contas_sem_dre_n2:
            print(f"   {row.conta_pai}: R$ {row.valor_total:,.2f}")
        
        # Verificar fluxo completo
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as registros_fluxo,
                SUM(fd.valor_original) as valor_total_fluxo
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND ds2.is_active = true
            AND fd.valor_original IS NOT NULL
        """), {"empresa_id": empresa_id})
        
        fluxo_data = result.fetchone()
        print(f"\n📊 FLUXO COMPLETO APÓS CORREÇÃO:")
        print(f"   Registros: {fluxo_data.registros_fluxo}")
        print(f"   Valor total: R$ {fluxo_data.valor_total_fluxo:,.2f}")
        
        # Verificar view
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as registros_view,
                SUM(valor_total) as valor_total_view
            FROM v_dre_n0_completo
            WHERE empresa_id = :empresa_id
        """), {"empresa_id": empresa_id})
        
        view_data = result.fetchone()
        print(f"\n📊 VIEW APÓS CORREÇÃO:")
        print(f"   Registros: {view_data.registros_view}")
        print(f"   Valor total: R$ {view_data.valor_total_view:,.2f}")
        
        # Calcular diferença
        diferenca = view_data.valor_total_view - fluxo_data.valor_total_fluxo
        percentual = (diferenca / abs(fluxo_data.valor_total_fluxo)) * 100 if fluxo_data.valor_total_fluxo != 0 else 0
        print(f"\n📊 DIFERENÇA FINAL:")
        print(f"   Valor: R$ {diferenca:,.2f}")
        print(f"   Percentual: {percentual:+.1f}%")
        
        if abs(percentual) < 1:
            print("   ✅ SUCESSO! Diferença menor que 1%")
        else:
            print("   ❌ Ainda há diferença significativa")
        
        print("\n3️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 CORREÇÃO CONCLUÍDA!")
        print("\n💡 MELHORIAS IMPLEMENTADAS:")
        print("   1. Contas específicas foram mapeadas para DRE N2")
        print("   2. Movimentação entre contas → Receitas/Despesas não recorrentes")
        print("   3. Empréstimos Bancários → Receitas/Despesas não recorrentes")
        print("   4. View agora deve capturar todos os valores")
        print("   5. Diferença deve estar dentro do esperado (< 1%)")

if __name__ == "__main__":
    main()
