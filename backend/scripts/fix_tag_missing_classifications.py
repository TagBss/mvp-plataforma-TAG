#!/usr/bin/env python3
"""
Script para identificar e mapear classificações faltantes das empresas TAG
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 IDENTIFICANDO CLASSIFICAÇÕES FALTANTES DAS EMPRESAS TAG")
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
            
            print("\n1️⃣ VERIFICANDO CLASSIFICAÇÕES SEM MAPEAMENTO")
            print("-" * 60)
            
            # Verificar classificações que não têm mapeamento
            result = conn.execute(text("""
                SELECT DISTINCT
                    fd.classificacao,
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                AND (dp.descricao_origem IS NULL OR dp.descricao_origem::text = '')
                GROUP BY fd.classificacao
                ORDER BY valor_total DESC
                LIMIT 20
            """), {"empresa_id": empresa_id})
            
            sem_mapeamento = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES SEM MAPEAMENTO: {len(sem_mapeamento)}")
            for row in sem_mapeamento:
                print(f"   {row.classificacao}: {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n2️⃣ VERIFICANDO CLASSIFICAÇÕES COM MAPEAMENTO INCOMPLETO")
            print("-" * 60)
            
            # Verificar classificações que têm mapeamento mas não chegam ao plano_de_contas
            result = conn.execute(text("""
                SELECT DISTINCT
                    fd.classificacao,
                    dp.descricao_origem,
                    dp.descricao_destino,
                    pc.conta_pai,
                    pc.classificacao_dre_n2,
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                AND dp.descricao_origem IS NOT NULL
                AND (pc.conta_pai IS NULL OR pc.classificacao_dre_n2 IS NULL)
                GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
                ORDER BY valor_total DESC
                LIMIT 20
            """), {"empresa_id": empresa_id})
            
            mapeamento_incompleto = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM MAPEAMENTO INCOMPLETO: {len(mapeamento_incompleto)}")
            for row in mapeamento_incompleto:
                status = "❌ SEM CONTA" if row.conta_pai is None else "❌ SEM CLASSIFICAÇÃO"
                print(f"   {row.classificacao} → {row.descricao_destino} | {status} | {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n3️⃣ VERIFICANDO PLANOS_DE_CONTAS DISPONÍVEIS")
            print("-" * 60)
            
            # Verificar planos_de_contas disponíveis
            result = conn.execute(text("""
                SELECT 
                    conta_pai,
                    classificacao_dre_n2,
                    COUNT(*) as total
                FROM plano_de_contas
                WHERE classificacao_dre_n2 IS NOT NULL
                AND classificacao_dre_n2::text <> ''
                GROUP BY conta_pai, classificacao_dre_n2
                ORDER BY classificacao_dre_n2, conta_pai
            """))
            
            planos_disponiveis = result.fetchall()
            print(f"📊 PLANOS_DE_CONTAS COM CLASSIFICAÇÃO: {len(planos_disponiveis)}")
            for row in planos_disponiveis:
                print(f"   {row.conta_pai} → {row.classificacao_dre_n2}")
            
            print("\n4️⃣ VERIFICANDO DIFERENÇA ENTRE DRE N2 E CLASSIFICAÇÕES")
            print("-" * 60)
            
            # Verificar diferença entre DRE N2 e classificações
            result = conn.execute(text("""
                WITH dre_n2_totais AS (
                    SELECT 
                        pc.classificacao_dre_n2,
                        SUM(fd.valor_original) as valor_total_dre_n2
                    FROM financial_data fd
                    LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND pc.classificacao_dre_n2::text <> ''
                    GROUP BY pc.classificacao_dre_n2
                ),
                classificacoes_totais AS (
                    SELECT 
                        pc.classificacao_dre_n2,
                        SUM(fd.valor_original) as valor_total_classificacoes
                    FROM financial_data fd
                    LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    LEFT JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND pc.classificacao_dre_n2::text <> ''
                    AND ds2.is_active = true
                    GROUP BY pc.classificacao_dre_n2
                )
                SELECT 
                    COALESCE(dn2.classificacao_dre_n2, cl.classificacao_dre_n2) as classificacao,
                    dn2.valor_total_dre_n2,
                    cl.valor_total_classificacoes,
                    COALESCE(dn2.valor_total_dre_n2, 0) - COALESCE(cl.valor_total_classificacoes, 0) as diferenca
                FROM dre_n2_totais dn2
                FULL OUTER JOIN classificacoes_totais cl ON dn2.classificacao_dre_n2 = cl.classificacao_dre_n2
                WHERE COALESCE(dn2.valor_total_dre_n2, 0) <> COALESCE(cl.valor_total_classificacoes, 0)
                ORDER BY ABS(COALESCE(dn2.valor_total_dre_n2, 0) - COALESCE(cl.valor_total_classificacoes, 0)) DESC
            """), {"empresa_id": empresa_id})
            
            diferencas = result.fetchall()
            print(f"📊 DIFERENÇAS ENCONTRADAS: {len(diferencas)}")
            for row in diferencas:
                print(f"   {row.classificacao}:")
                print(f"     DRE N2: R$ {row.valor_total_dre_n2:,.2f}")
                print(f"     Classificações: R$ {row.valor_total_classificacoes:,.2f}")
                print(f"     Diferença: R$ {row.diferenca:,.2f}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 PROBLEMA IDENTIFICADO:")
        print("   • As empresas TAG têm classificações sem mapeamento completo")
        print("   • Algumas classificações não chegam ao plano_de_contas")
        print("   • Resultado: DRE N2 e classificações não batem")
        print("\n💡 SOLUÇÕES:")
        print("   1. Mapear classificações sem de_para")
        print("   2. Completar mapeamentos incompletos")
        print("   3. Verificar se todos os planos_de_contas estão corretos")

if __name__ == "__main__":
    main()
