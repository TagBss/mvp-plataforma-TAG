#!/usr/bin/env python3
"""
Script para verificar se o JOIN da view está funcionando corretamente
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO CORRESPONDÊNCIA DO JOIN NA VIEW")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO CORRESPONDÊNCIA DRE_STRUCTURE_N0 ↔ VALORES_AGREGADOS")
        print("-" * 60)
        
        empresas_tag = [
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar correspondência entre dre_structure_n0 e valores_agregados
            result = conn.execute(text("""
                WITH valores_agregados AS (
                    SELECT 
                        pc.classificacao_dre_n2 AS nome_conta,
                        pc.classificacao_dre_n2 AS descricao,
                        dl.empresa_id,
                        SUM(dl.valor_original) AS valor_total
                    FROM financial_data fd
                    JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                    JOIN (
                        SELECT id, classificacao, valor_original, empresa_id
                        FROM financial_data
                        WHERE valor_original IS NOT NULL 
                        AND competencia IS NOT NULL 
                        AND empresa_id IS NOT NULL
                    ) dl ON fd.id = dl.id
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND ds2.is_active = true
                    GROUP BY pc.classificacao_dre_n2, dl.empresa_id
                )
                SELECT 
                    ds0.description as dre_n0_desc,
                    va.nome_conta as valores_nome,
                    ds0.description = va.nome_conta as corresponde,
                    ds0.is_active as dre_n0_ativo,
                    va.valor_total
                FROM dre_structure_n0 ds0
                LEFT JOIN valores_agregados va ON ds0.description = va.nome_conta AND ds0.empresa_id = va.empresa_id
                WHERE ds0.empresa_id = :empresa_id
                ORDER BY ds0.order_index
            """), {"empresa_id": empresa_id})
            
            correspondencias = result.fetchall()
            print(f"   📊 CORRESPONDÊNCIAS:")
            
            correspondem = 0
            nao_correspondem = 0
            com_valores = 0
            
            for row in correspondencias:
                status = "✅" if row.corresponde else "❌"
                valor = f"R$ {row.valor_total:,.2f}" if row.valor_total else "R$ 0,00"
                
                if row.corresponde:
                    correspondem += 1
                else:
                    nao_correspondem += 1
                
                if row.valor_total and row.valor_total != 0:
                    com_valores += 1
                
                print(f"     {status} {row.dre_n0_desc} = {row.valores_nome} | {valor}")
            
            print(f"   📈 RESUMO:")
            print(f"     Correspondem: {correspondem}")
            print(f"     Não correspondem: {nao_correspondem}")
            print(f"     Com valores: {com_valores}")
        
        print("\n2️⃣ VERIFICANDO DIFERENÇAS NAS DESCRIÇÕES")
        print("-" * 60)
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar descrições que não correspondem
            result = conn.execute(text("""
                WITH valores_agregados AS (
                    SELECT 
                        pc.classificacao_dre_n2 AS nome_conta,
                        dl.empresa_id,
                        SUM(dl.valor_original) AS valor_total
                    FROM financial_data fd
                    JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                    JOIN (
                        SELECT id, classificacao, valor_original, empresa_id
                        FROM financial_data
                        WHERE valor_original IS NOT NULL 
                        AND competencia IS NOT NULL 
                        AND empresa_id IS NOT NULL
                    ) dl ON fd.id = dl.id
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND ds2.is_active = true
                    GROUP BY pc.classificacao_dre_n2, dl.empresa_id
                )
                SELECT 
                    ds0.description as dre_n0_desc,
                    va.nome_conta as valores_nome,
                    va.valor_total
                FROM dre_structure_n0 ds0
                LEFT JOIN valores_agregados va ON ds0.description = va.nome_conta AND ds0.empresa_id = va.empresa_id
                WHERE ds0.empresa_id = :empresa_id
                AND (va.nome_conta IS NULL OR ds0.description != va.nome_conta)
                ORDER BY ds0.order_index
            """), {"empresa_id": empresa_id})
            
            diferencas = result.fetchall()
            print(f"   📊 DESCRIÇÕES QUE NÃO CORRESPONDEM: {len(diferencas)}")
            for row in diferencas:
                valor = f"R$ {row.valor_total:,.2f}" if row.valor_total else "R$ 0,00"
                print(f"     DRE N0: '{row.dre_n0_desc}'")
                print(f"     Valores: '{row.valores_nome}' | {valor}")
        
        print("\n3️⃣ VERIFICANDO BLUEFIT PARA COMPARAÇÃO")
        print("-" * 60)
        
        # Verificar Bluefit para comparação
        result = conn.execute(text("""
            WITH valores_agregados AS (
                SELECT 
                    pc.classificacao_dre_n2 AS nome_conta,
                    dl.empresa_id,
                    SUM(dl.valor_original) AS valor_total
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                JOIN (
                    SELECT id, classificacao, valor_original, empresa_id
                    FROM financial_data
                    WHERE valor_original IS NOT NULL 
                    AND competencia IS NOT NULL 
                    AND empresa_id IS NOT NULL
                ) dl ON fd.id = dl.id
                WHERE fd.empresa_id = '2fd835d0-c899-49f4-9096-9fdc3e4d3008'
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND ds2.is_active = true
                GROUP BY pc.classificacao_dre_n2, dl.empresa_id
            )
            SELECT 
                COUNT(*) as total_contas,
                COUNT(CASE WHEN va.nome_conta IS NOT NULL THEN 1 END) as com_correspondencia,
                COUNT(CASE WHEN va.valor_total IS NOT NULL AND va.valor_total != 0 THEN 1 END) as com_valores,
                SUM(va.valor_total) as valor_total
            FROM dre_structure_n0 ds0
            LEFT JOIN valores_agregados va ON ds0.description = va.nome_conta AND ds0.empresa_id = va.empresa_id
            WHERE ds0.empresa_id = '2fd835d0-c899-49f4-9096-9fdc3e4d3008'
        """))
        
        bluefit_data = result.fetchone()
        print(f"📊 BLUEFIT:")
        print(f"   Total contas: {bluefit_data.total_contas}")
        print(f"   Com correspondência: {bluefit_data.com_correspondencia}")
        print(f"   Com valores: {bluefit_data.com_valores}")
        print(f"   Valor total: R$ {bluefit_data.valor_total:,.2f}")
        
        print("\n4️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Descrições entre DRE N0 e valores_agregados não correspondem")
        print("   2. JOIN da view pode estar falhando por diferenças de texto")
        print("   3. Valores podem estar sendo perdidos no JOIN")
        print("   4. View pode precisar de ajuste na lógica de correspondência")

if __name__ == "__main__":
    main()
