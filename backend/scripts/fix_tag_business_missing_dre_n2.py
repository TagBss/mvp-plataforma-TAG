#!/usr/bin/env python3
"""
Script para corrigir o problema da TAG Business Solutions mapeando contas sem DRE N2
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 CORRIGINDO PROBLEMA DA TAG BUSINESS SOLUTIONS")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresa_id = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        empresa_nome = "TAG Business Solutions"
        
        print(f"\n🏢 {empresa_nome} ({empresa_id})")
        
        print("\n1️⃣ IDENTIFICANDO CONTAS SEM DRE N2")
        print("-" * 60)
        
        # Identificar contas sem DRE N2
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
        print(f"📊 CONTAS SEM DRE N2: {len(contas_sem_dre_n2)}")
        
        total_perdido = 0
        for row in contas_sem_dre_n2:
            print(f"   {row.conta_pai}: R$ {row.valor_total:,.2f}")
            total_perdido += row.valor_total
        
        print(f"\n💰 VALOR TOTAL PERDIDO: R$ {total_perdido:,.2f}")
        
        print("\n2️⃣ MAPEANDO CONTAS PARA DRE N2 APROPRIADAS")
        print("-" * 60)
        
        # Mapear contas baseado em padrões
        mapeamentos = {
            # Contas de receita
            "[ 2.06.001 ] Rendimento de aplicação": "( + ) Receitas Financeiras",
            "[ 2.06.002 ] TAG Brands": "( + ) Receitas Financeiras",
            
            # Contas de despesa
            "[ 2.05.003 ] Integralização de Cotas": "( - ) Despesas Administrativas",
            "[ 5.005 ] Veículos - Novos e Usados": "( - ) Despesas Administrativas",
            "[ 2.02.003 ] Sala de Recreação": "( - ) Despesas Administrativas",
            "[ 2.02.001 ] Instalações": "( - ) Despesas Administrativas",
            
            # Contas de investimento/financiamento
            "[ 3.01.001 ] Empréstimos Bancários": "( + / - ) Receitas / Despesas não recorrentes",
            "[ 3.04.001 ] Aporte Sócios": "( + / - ) Receitas / Despesas não recorrentes",
            "[ 2.02.004 ] Venda de Imobilizado": "( + / - ) Receitas / Despesas não recorrentes",
            
            # Conta de movimentação interna
            "[ 4.01.002 ] Movimentação entre contas": "( + / - ) Receitas / Despesas não recorrentes"
        }
        
        print("📊 MAPEAMENTOS PROPOSTOS:")
        for conta_origem, conta_destino in mapeamentos.items():
            print(f"   {conta_origem} → {conta_destino}")
        
        print("\n3️⃣ APLICANDO MAPEAMENTOS")
        print("-" * 60)
        
        # Aplicar os mapeamentos
        for conta_origem, conta_destino in mapeamentos.items():
            print(f"🔄 Mapeando {conta_origem} → {conta_destino}")
            
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
            else:
                print(f"   ❌ Conta destino não encontrada: {conta_destino}")
        
        print("\n4️⃣ VERIFICANDO RESULTADO")
        print("-" * 60)
        
        # Verificar se ainda há contas sem DRE N2
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as contas_sem_dre_n2,
                SUM(fd.valor_original) as valor_total_sem_dre_n2
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 IS NULL
            AND fd.valor_original IS NOT NULL
        """), {"empresa_id": empresa_id})
        
        resultado = result.fetchone()
        print(f"📊 RESULTADO APÓS CORREÇÃO:")
        print(f"   Contas sem DRE N2: {resultado.contas_sem_dre_n2}")
        print(f"   Valor total sem DRE N2: R$ {resultado.valor_total_sem_dre_n2:,.2f}")
        
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
        print(f"   Fluxo completo: {fluxo_data.registros_fluxo} registros, R$ {fluxo_data.valor_total_fluxo:,.2f}")
        
        # Verificar view
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as registros_view,
                SUM(valor_total) as valor_total_view
            FROM v_dre_n0_completo
            WHERE empresa_id = :empresa_id
        """), {"empresa_id": empresa_id})
        
        view_data = result.fetchone()
        print(f"   View: {view_data.registros_view} registros, R$ {view_data.valor_total_view:,.2f}")
        
        # Calcular diferença
        diferenca = view_data.valor_total_view - fluxo_data.valor_total_fluxo
        percentual = (diferenca / abs(fluxo_data.valor_total_fluxo)) * 100 if fluxo_data.valor_total_fluxo != 0 else 0
        print(f"   Diferença: R$ {diferenca:,.2f} ({percentual:+.1f}%)")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 CORREÇÃO CONCLUÍDA!")
        print("\n💡 MELHORIAS IMPLEMENTADAS:")
        print("   1. Contas sem DRE N2 foram mapeadas para contas apropriadas")
        print("   2. Movimentações internas foram direcionadas para receitas/despesas não recorrentes")
        print("   3. Receitas financeiras foram consolidadas")
        print("   4. Despesas administrativas foram consolidadas")
        print("   5. View agora deve capturar todos os valores")

if __name__ == "__main__":
    main()
