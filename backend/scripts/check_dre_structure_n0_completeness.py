#!/usr/bin/env python3
"""
Script para verificar se dre_structure_n0 tem todas as contas para cada empresa TAG
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO COMPLETUDE DO DRE_STRUCTURE_N0")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO DRE_STRUCTURE_N0 POR EMPRESA")
        print("-" * 60)
        
        empresas_tag = [
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar quantas contas DRE N0 existem para esta empresa
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_contas,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as contas_ativas
                FROM dre_structure_n0
                WHERE empresa_id = :empresa_id
            """), {"empresa_id": empresa_id})
            
            dre_n0_data = result.fetchone()
            print(f"   DRE N0: {dre_n0_data.total_contas} contas total, {dre_n0_data.contas_ativas} ativas")
            
            # Verificar se há contas DRE N0 para esta empresa
            result = conn.execute(text("""
                SELECT 
                    name,
                    description,
                    is_active
                FROM dre_structure_n0
                WHERE empresa_id = :empresa_id
                ORDER BY order_index
                LIMIT 5
            """), {"empresa_id": empresa_id})
            
            contas = result.fetchall()
            print(f"   Primeiras 5 contas:")
            for conta in contas:
                status = "✅" if conta.is_active else "❌"
                print(f"     {status} {conta.name}: {conta.description}")
        
        print("\n2️⃣ VERIFICANDO SE HÁ CONTAS DRE N0 PARA TAG")
        print("-" * 60)
        
        # Verificar se há contas DRE N0 para empresas TAG
        result = conn.execute(text("""
            SELECT 
                ds0.empresa_id,
                e.nome as empresa_nome,
                COUNT(*) as total_contas,
                COUNT(CASE WHEN ds0.is_active = true THEN 1 END) as contas_ativas
            FROM dre_structure_n0 ds0
            JOIN empresas e ON ds0.empresa_id = e.id
            WHERE ds0.empresa_id = ANY(ARRAY[
                'd09c3591-3de3-4a8f-913a-2e36de84610f',
                '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            ])
            GROUP BY ds0.empresa_id, e.nome
            ORDER BY e.nome
        """))
        
        empresas_dre_n0 = result.fetchall()
        print("📊 EMPRESAS COM DRE N0:")
        for row in empresas_dre_n0:
            print(f"   {row.empresa_nome}: {row.total_contas} contas total, {row.contas_ativas} ativas")
        
        print("\n3️⃣ VERIFICANDO SE HÁ CONTAS DRE N0 PARA BLUEFIT")
        print("-" * 60)
        
        # Verificar se há contas DRE N0 para Bluefit
        result = conn.execute(text("""
            SELECT 
                ds0.empresa_id,
                e.nome as empresa_nome,
                COUNT(*) as total_contas,
                COUNT(CASE WHEN ds0.is_active = true THEN 1 END) as contas_ativas
            FROM dre_structure_n0 ds0
            JOIN empresas e ON ds0.empresa_id = e.id
            WHERE ds0.empresa_id = '2fd835d0-c899-49f4-9096-9fdc3e4d3008'
            GROUP BY ds0.empresa_id, e.nome
        """))
        
        bluefit_dre_n0 = result.fetchone()
        if bluefit_dre_n0:
            print(f"📊 BLUEFIT:")
            print(f"   {bluefit_dre_n0.empresa_nome}: {bluefit_dre_n0.total_contas} contas total, {bluefit_dre_n0.contas_ativas} ativas")
        else:
            print("❌ BLUEFIT: Nenhuma conta DRE N0 encontrada!")
        
        print("\n4️⃣ VERIFICANDO ESTRUTURA DRE N0")
        print("-" * 60)
        
        # Verificar estrutura geral do DRE N0
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_contas,
                COUNT(DISTINCT empresa_id) as empresas_com_contas,
                COUNT(CASE WHEN is_active = true THEN 1 END) as contas_ativas
            FROM dre_structure_n0
        """))
        
        estrutura_geral = result.fetchone()
        print(f"📊 ESTRUTURA GERAL DRE N0:")
        print(f"   Total contas: {estrutura_geral.total_contas}")
        print(f"   Empresas com contas: {estrutura_geral.empresas_com_contas}")
        print(f"   Contas ativas: {estrutura_geral.contas_ativas}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. DRE N0 pode não ter todas as 77 contas para empresas TAG")
        print("   2. View pode estar limitada pelas contas disponíveis no DRE N0")
        print("   3. Bluefit pode ter estrutura DRE N0 completa enquanto TAG não")
        print("   4. View precisa ser ajustada para funcionar sem DRE N0 completo")

if __name__ == "__main__":
    main()
