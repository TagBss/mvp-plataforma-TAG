#!/usr/bin/env python3
"""
Script para verificar a estrutura da view v_dre_n0_completo
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO ESTRUTURA DA VIEW V_DRE_N0_COMPLETO")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO ESTRUTURA DA VIEW")
        print("-" * 60)
        
        # Verificar a estrutura da view
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'v_dre_n0_completo'
            ORDER BY ordinal_position
        """))
        
        colunas = result.fetchall()
        print(f"📊 COLUNAS DA VIEW: {len(colunas)}")
        for coluna in colunas:
            print(f"   {coluna.column_name}: {coluna.data_type}")
        
        print("\n2️⃣ VERIFICANDO DEFINIÇÃO DA VIEW")
        print("-" * 60)
        
        # Verificar a definição da view
        result = conn.execute(text("""
            SELECT definition
            FROM pg_views
            WHERE viewname = 'v_dre_n0_completo'
        """))
        
        definicao = result.fetchone()
        if definicao:
            print("📊 DEFINIÇÃO DA VIEW:")
            print(definicao.definition)
        else:
            print("❌ View não encontrada")
        
        print("\n3️⃣ VERIFICANDO DADOS NA VIEW")
        print("-" * 60)
        
        # Verificar dados na view
        result = conn.execute(text("""
            SELECT 
                dre_n0_id,
                dre_n1_id,
                dre_n2_id,
                empresa_id,
                valor_original,
                COUNT(*) as total_registros
            FROM v_dre_n0_completo
            WHERE empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            GROUP BY dre_n0_id, dre_n1_id, dre_n2_id, empresa_id, valor_original
            ORDER BY total_registros DESC
            LIMIT 10
        """))
        
        dados_view = result.fetchall()
        print(f"📊 DADOS NA VIEW: {len(dados_view)}")
        for row in dados_view:
            print(f"   DRE N0: {row.dre_n0_id}, DRE N1: {row.dre_n1_id}, DRE N2: {row.dre_n2_id}")
            print(f"     Valor: R$ {row.valor_original:,.2f}, Registros: {row.total_registros}")
        
        print("\n4️⃣ VERIFICANDO JOIN COM DRE_STRUCTURE_N2")
        print("-" * 60)
        
        # Verificar se o join com dre_structure_n2 está funcionando
        result = conn.execute(text("""
            SELECT 
                va.dre_n2_id,
                ds2.description,
                COUNT(*) as total_registros,
                SUM(va.valor_original) as valor_total
            FROM v_dre_n0_completo va
            LEFT JOIN dre_structure_n2 ds2 ON va.dre_n2_id = ds2.id
            WHERE va.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND va.valor_original IS NOT NULL
            GROUP BY va.dre_n2_id, ds2.description
            ORDER BY valor_total DESC
            LIMIT 10
        """))
        
        join_dre_n2 = result.fetchall()
        print(f"📊 JOIN COM DRE_STRUCTURE_N2: {len(join_dre_n2)}")
        for row in join_dre_n2:
            print(f"   DRE N2 ID: {row.dre_n2_id}, Descrição: {row.description}")
            print(f"     Valor: R$ {row.valor_total:,.2f}, Registros: {row.total_registros}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Se a view não tem dre_n2_id, precisamos corrigir a view")
        print("   2. Se a view tem dre_n2_id, o problema pode estar no join")
        print("   3. Verificar se os dados estão sendo agregados corretamente")

if __name__ == "__main__":
    main()
