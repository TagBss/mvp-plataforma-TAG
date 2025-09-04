#!/usr/bin/env python3
"""
Script para verificar se a view v_dre_n0_completo está filtrando corretamente por empresa
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO FILTRO POR EMPRESA NA VIEW")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO ESTRUTURA DA VIEW")
        print("-" * 60)
        
        # Verificar se a view está filtrando por empresa_id
        result = conn.execute(text("""
            SELECT pg_get_viewdef('v_dre_n0_completo', true)
        """))
        
        view_definition = result.fetchone()[0]
        print("📊 DEFINIÇÃO DA VIEW:")
        print(view_definition)
        
        print("\n2️⃣ VERIFICANDO DADOS POR EMPRESA TAG")
        print("-" * 60)
        
        # Verificar dados por empresa TAG
        empresas_tag = [
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar dados na view
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(valor_total) as valor_total,
                    COUNT(DISTINCT dre_n0_id) as contas_dre_n0
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
            """), {"empresa_id": empresa_id})
            
            view_data = result.fetchone()
            print(f"   View: {view_data.total_registros} registros, R$ {view_data.valor_total:,.2f}")
            print(f"   Contas DRE N0: {view_data.contas_dre_n0}")
            
            # Verificar dados diretos do fluxo
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total,
                    COUNT(DISTINCT pc.classificacao_dre_n2) as contas_dre_n2
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                WHERE fd.empresa_id = :empresa_id
                AND pc.classificacao_dre_n2 IS NOT NULL
                AND fd.valor_original IS NOT NULL
            """), {"empresa_id": empresa_id})
            
            fluxo_data = result.fetchone()
            print(f"   Fluxo: {fluxo_data.total_registros} registros, R$ {fluxo_data.valor_total:,.2f}")
            print(f"   Contas DRE N2: {fluxo_data.contas_dre_n2}")
            
            # Verificar diferença
            diferenca = view_data.valor_total - fluxo_data.valor_total
            print(f"   Diferença: R$ {diferenca:,.2f}")
        
        print("\n3️⃣ VERIFICANDO SE HÁ MISTURA DE DADOS")
        print("-" * 60)
        
        # Verificar se há dados de outras empresas na view
        result = conn.execute(text("""
            SELECT 
                empresa_id,
                e.nome as empresa_nome,
                COUNT(*) as registros,
                SUM(valor_total) as valor_total
            FROM v_dre_n0_completo v
            JOIN empresas e ON v.empresa_id = e.id
            WHERE v.empresa_id = ANY(ARRAY[
                'd09c3591-3de3-4a8f-913a-2e36de84610f',
                '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            ])
            GROUP BY empresa_id, e.nome
            ORDER BY valor_total DESC
        """))
        
        empresas_na_view = result.fetchall()
        print("📊 EMPRESAS NA VIEW:")
        for row in empresas_na_view:
            print(f"   {row.empresa_nome}: {row.registros} registros, R$ {row.valor_total:,.2f}")
        
        print("\n4️⃣ VERIFICANDO GRUPO EMPRESA")
        print("-" * 60)
        
        # Verificar se a view está considerando grupo_empresa_id
        result = conn.execute(text("""
            SELECT 
                e.grupo_empresa_id,
                COUNT(DISTINCT e.id) as empresas_no_grupo,
                COUNT(*) as total_registros,
                SUM(v.valor_total) as valor_total
            FROM v_dre_n0_completo v
            JOIN empresas e ON v.empresa_id = e.id
            WHERE e.grupo_empresa_id = '41054e58-53fb-4402-8ac1-a202f56bb8f5'
            GROUP BY e.grupo_empresa_id
        """))
        
        grupo_data = result.fetchone()
        if grupo_data:
            print(f"📊 GRUPO TAG:")
            print(f"   Empresas no grupo: {grupo_data.empresas_no_grupo}")
            print(f"   Total registros: {grupo_data.total_registros}")
            print(f"   Valor total: R$ {grupo_data.valor_total:,.2f}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. View pode estar misturando dados entre empresas do mesmo grupo")
        print("   2. Filtro por empresa_id pode não estar funcionando corretamente")
        print("   3. Join com empresas pode estar causando duplicação")
        print("   4. View pode estar considerando grupo_empresa_id em vez de empresa_id")

if __name__ == "__main__":
    main()
