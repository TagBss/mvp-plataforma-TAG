#!/usr/bin/env python3
"""
Script para analisar o fluxo que está funcionando para classificações e nome
e aplicar a mesma lógica para DRE N2
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 ANALISANDO FLUXO QUE ESTÁ FUNCIONANDO")
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
            
            print("\n1️⃣ VERIFICANDO FLUXO QUE ESTÁ FUNCIONANDO (CLASSIFICAÇÕES)")
            print("-" * 60)
            
            # Verificar o fluxo que está funcionando para classificações
            result = conn.execute(text("""
                SELECT 
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
                AND pc.conta_pai IS NOT NULL
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND pc.classificacao_dre_n2::text <> ''
                GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
                ORDER BY valor_total DESC
                LIMIT 10
            """), {"empresa_id": empresa_id})
            
            fluxo_funcionando = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM FLUXO COMPLETO: {len(fluxo_funcionando)}")
            for row in fluxo_funcionando:
                print(f"   {row.classificacao} → {row.descricao_destino} → {row.classificacao_dre_n2}")
                print(f"     {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n2️⃣ VERIFICANDO FLUXO QUE NÃO ESTÁ FUNCIONANDO (DRE N2)")
            print("-" * 60)
            
            # Verificar o fluxo que não está funcionando para DRE N2
            result = conn.execute(text("""
                SELECT 
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
                AND (pc.conta_pai IS NULL OR pc.classificacao_dre_n2 IS NULL OR pc.classificacao_dre_n2::text = '')
                GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
                ORDER BY valor_total DESC
                LIMIT 10
            """), {"empresa_id": empresa_id})
            
            fluxo_nao_funcionando = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM FLUXO INCOMPLETO: {len(fluxo_nao_funcionando)}")
            for row in fluxo_nao_funcionando:
                status = "❌ SEM CONTA" if row.conta_pai is None else "❌ SEM CLASSIFICAÇÃO DRE N2"
                print(f"   {row.classificacao} → {row.descricao_destino} | {status}")
                print(f"     {row.total_registros} registros, R$ {row.valor_total:,.2f}")
            
            print("\n3️⃣ VERIFICANDO DRE_STRUCTURE_N2 DISPONÍVEL")
            print("-" * 60)
            
            # Verificar quais DRE N2 estão disponíveis
            result = conn.execute(text("""
                SELECT 
                    description,
                    is_active,
                    COUNT(*) as total
                FROM dre_structure_n2
                WHERE is_active = true
                GROUP BY description, is_active
                ORDER BY description
            """))
            
            dre_n2_disponiveis = result.fetchall()
            print(f"📊 DRE N2 DISPONÍVEIS: {len(dre_n2_disponiveis)}")
            for row in dre_n2_disponiveis:
                print(f"   {row.description}")
            
            print("\n4️⃣ VERIFICANDO CORRESPONDÊNCIA PLANO_DE_CONTAS → DRE_STRUCTURE_N2")
            print("-" * 60)
            
            # Verificar correspondência entre plano_de_contas e dre_structure_n2
            result = conn.execute(text("""
                SELECT 
                    pc.classificacao_dre_n2,
                    ds2.description,
                    ds2.is_active,
                    COUNT(*) as total
                FROM plano_de_contas pc
                LEFT JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                WHERE pc.classificacao_dre_n2 IS NOT NULL
                AND pc.classificacao_dre_n2::text <> ''
                GROUP BY pc.classificacao_dre_n2, ds2.description, ds2.is_active
                ORDER BY pc.classificacao_dre_n2
            """))
            
            correspondencias = result.fetchall()
            print(f"📊 CORRESPONDÊNCIAS: {len(correspondencias)}")
            
            sem_correspondencia = 0
            com_correspondencia = 0
            
            for row in correspondencias:
                if row.description is None:
                    print(f"   ❌ {row.classificacao_dre_n2} → SEM CORRESPONDÊNCIA")
                    sem_correspondencia += 1
                else:
                    status = "✅ ATIVA" if row.is_active else "❌ INATIVA"
                    print(f"   {status} {row.classificacao_dre_n2} → {row.description}")
                    com_correspondencia += 1
            
            print(f"\n📊 RESUMO:")
            print(f"   ✅ Com correspondência: {com_correspondencia}")
            print(f"   ❌ Sem correspondência: {sem_correspondencia}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 ANÁLISE CONCLUÍDA!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Identificar classificações que não têm correspondência no dre_structure_n2")
        print("   2. Criar as correspondências faltantes")
        print("   3. Verificar se os valores do DRE N2 agora batem com as classificações")

if __name__ == "__main__":
    main()
