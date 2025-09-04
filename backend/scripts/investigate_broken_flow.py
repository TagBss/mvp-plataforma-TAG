#!/usr/bin/env python3
"""
Script para investigar o fluxo quebrado entre de_para e plano_de_contas
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 INVESTIGANDO FLUXO QUEBRADO")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresa_id = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        
        print("\n1️⃣ VERIFICANDO FLUXO COMPLETO")
        print("-" * 60)
        
        # Verificar fluxo completo
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
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND fd.valor_original IS NOT NULL
            GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
            ORDER BY valor_total DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        fluxo_completo = result.fetchall()
        print("📊 FLUXO COMPLETO (TOP 10):")
        for row in fluxo_completo:
            status = "✅" if row.conta_pai else "❌"
            print(f"   {status} {row.classificacao}")
            print(f"     De_para: {row.descricao_origem} → {row.descricao_destino}")
            print(f"     Plano: {row.conta_pai} → {row.classificacao_dre_n2}")
            print(f"     Valor: R$ {row.valor_total:,.2f}")
        
        print("\n2️⃣ VERIFICANDO CONTAS SEM PLANO_DE_CONTAS")
        print("-" * 60)
        
        # Verificar contas que não têm plano_de_contas
        result = conn.execute(text("""
            SELECT 
                dp.descricao_destino,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND pc.conta_pai IS NULL
            AND fd.valor_original IS NOT NULL
            GROUP BY dp.descricao_destino
            ORDER BY valor_total DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        contas_sem_plano = result.fetchall()
        print(f"📊 CONTAS SEM PLANO_DE_CONTAS: {len(contas_sem_plano)}")
        for row in contas_sem_plano:
            print(f"   {row.descricao_destino}: R$ {row.valor_total:,.2f}")
        
        print("\n3️⃣ VERIFICANDO CONTAS COM PLANO_DE_CONTAS")
        print("-" * 60)
        
        # Verificar contas que têm plano_de_contas
        result = conn.execute(text("""
            SELECT 
                dp.descricao_destino,
                pc.conta_pai,
                pc.classificacao_dre_n2,
                COUNT(*) as total_registros,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = :empresa_id
            AND fd.valor_original IS NOT NULL
            GROUP BY dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
            ORDER BY valor_total DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        contas_com_plano = result.fetchall()
        print(f"📊 CONTAS COM PLANO_DE_CONTAS: {len(contas_com_plano)}")
        for row in contas_com_plano:
            status = "✅" if row.classificacao_dre_n2 else "❌"
            print(f"   {status} {row.descricao_destino}")
            print(f"     Plano: {row.conta_pai} → {row.classificacao_dre_n2}")
            print(f"     Valor: R$ {row.valor_total:,.2f}")
        
        print("\n4️⃣ VERIFICANDO DIFERENÇAS DE NOMENCLATURA")
        print("-" * 60)
        
        # Verificar se há diferenças de nomenclatura
        result = conn.execute(text("""
            SELECT 
                dp.descricao_destino as de_para_destino,
                pc.conta_pai as plano_conta_pai,
                COUNT(*) as total_registros
            FROM de_para dp
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE dp.empresa_id = :empresa_id
            AND pc.conta_pai IS NULL
            GROUP BY dp.descricao_destino
            ORDER BY total_registros DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        diferencas_nomenclatura = result.fetchall()
        print(f"📊 DIFERENÇAS DE NOMENCLATURA: {len(diferencas_nomenclatura)}")
        for row in diferencas_nomenclatura:
            print(f"   De_para: {row.de_para_destino}")
            print(f"     Registros: {row.total_registros}")
        
        print("\n5️⃣ VERIFICANDO PLANO_DE_CONTAS DISPONÍVEL")
        print("-" * 60)
        
        # Verificar plano_de_contas disponível
        result = conn.execute(text("""
            SELECT 
                conta_pai,
                classificacao_dre_n2,
                COUNT(*) as total_registros
            FROM plano_de_contas
            WHERE empresa_id = :empresa_id
            ORDER BY conta_pai
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        plano_disponivel = result.fetchall()
        print(f"📊 PLANO_DE_CONTAS DISPONÍVEL (TOP 10):")
        for row in plano_disponivel:
            status = "✅" if row.classificacao_dre_n2 else "❌"
            print(f"   {status} {row.conta_pai} → {row.classificacao_dre_n2}")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 INVESTIGAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. De_para está apontando para contas que não existem no plano_de_contas")
        print("   2. Há diferenças de nomenclatura entre as tabelas")
        print("   3. Plano_de_contas pode estar incompleto")
        print("   4. Fluxo pode estar quebrado desde o início")

if __name__ == "__main__":
    main()
