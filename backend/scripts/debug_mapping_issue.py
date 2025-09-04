#!/usr/bin/env python3
"""
Script para debugar por que o mapeamento não está funcionando
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 DEBUGANDO PROBLEMA DE MAPEAMENTO")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        empresa_id = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        
        print("\n1️⃣ VERIFICANDO ESTRUTURA DA TABELA PLANO_DE_CONTAS")
        print("-" * 60)
        
        # Verificar estrutura da tabela
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'plano_de_contas'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print("📊 COLUNAS DA TABELA PLANO_DE_CONTAS:")
        for row in columns:
            print(f"   {row.column_name}: {row.data_type}")
        
        print("\n2️⃣ VERIFICANDO DADOS ESPECÍFICOS")
        print("-" * 60)
        
        # Verificar dados específicos
        result = conn.execute(text("""
            SELECT 
                conta_pai,
                classificacao_dre_n2,
                COUNT(*) as total_registros
            FROM plano_de_contas
            WHERE empresa_id = :empresa_id
            AND conta_pai IN (
                '[ 4.01.002 ] Movimentação entre contas',
                '[ 3.01.001 ] Empréstimos Bancários',
                '[ 3.04.001 ] Aporte Sócios'
            )
            GROUP BY conta_pai, classificacao_dre_n2
            ORDER BY conta_pai
        """), {"empresa_id": empresa_id})
        
        dados_especificos = result.fetchall()
        print("📊 DADOS ESPECÍFICOS:")
        for row in dados_especificos:
            print(f"   {row.conta_pai}: {row.classificacao_dre_n2} ({row.total_registros} registros)")
        
        print("\n3️⃣ VERIFICANDO SE HÁ MÚLTIPLOS REGISTROS")
        print("-" * 60)
        
        # Verificar se há múltiplos registros para a mesma conta
        result = conn.execute(text("""
            SELECT 
                conta_pai,
                COUNT(*) as total_registros,
                COUNT(DISTINCT classificacao_dre_n2) as classificacoes_diferentes
            FROM plano_de_contas
            WHERE empresa_id = :empresa_id
            GROUP BY conta_pai
            HAVING COUNT(*) > 1
            ORDER BY total_registros DESC
            LIMIT 10
        """), {"empresa_id": empresa_id})
        
        multiplos_registros = result.fetchall()
        print(f"📊 CONTAS COM MÚLTIPLOS REGISTROS: {len(multiplos_registros)}")
        for row in multiplos_registros:
            print(f"   {row.conta_pai}: {row.total_registros} registros, {row.classificacoes_diferentes} classificações")
        
        print("\n4️⃣ VERIFICANDO CONSTRAINT UNIQUE")
        print("-" * 60)
        
        # Verificar constraints
        result = conn.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'plano_de_contas'
            ORDER BY tc.constraint_name
        """))
        
        constraints = result.fetchall()
        print("📊 CONSTRAINTS PLANO_DE_CONTAS:")
        for row in constraints:
            print(f"   {row.constraint_name}: {row.constraint_type} ({row.column_name})")
        
        print("\n5️⃣ TESTANDO UPDATE MANUAL")
        print("-" * 60)
        
        # Testar update manual
        conta_teste = "[ 4.01.002 ] Movimentação entre contas"
        classificacao_teste = "( + / - ) Receitas / Despesas não recorrentes"
        
        print(f"🔄 Testando update: {conta_teste} → {classificacao_teste}")
        
        # Verificar antes do update
        result = conn.execute(text("""
            SELECT 
                conta_pai,
                classificacao_dre_n2,
                COUNT(*) as total_registros
            FROM plano_de_contas
            WHERE empresa_id = :empresa_id
            AND conta_pai = :conta_teste
            GROUP BY conta_pai, classificacao_dre_n2
        """), {"empresa_id": empresa_id, "conta_teste": conta_teste})
        
        antes = result.fetchall()
        print(f"   ANTES: {len(antes)} registros")
        for row in antes:
            print(f"     {row.conta_pai}: {row.classificacao_dre_n2} ({row.total_registros} registros)")
        
        # Fazer o update
        result = conn.execute(text("""
            UPDATE plano_de_contas
            SET classificacao_dre_n2 = :classificacao_teste
            WHERE conta_pai = :conta_teste
            AND empresa_id = :empresa_id
        """), {
            "classificacao_teste": classificacao_teste,
            "conta_teste": conta_teste,
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
            AND conta_pai = :conta_teste
            GROUP BY conta_pai, classificacao_dre_n2
        """), {"empresa_id": empresa_id, "conta_teste": conta_teste})
        
        depois = result.fetchall()
        print(f"   DEPOIS: {len(depois)} registros")
        for row in depois:
            print(f"     {row.conta_pai}: {row.classificacao_dre_n2} ({row.total_registros} registros)")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 DEBUG CONCLUÍDO!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Pode haver múltiplos registros para a mesma conta")
        print("   2. Constraint UNIQUE pode estar impedindo o update")
        print("   3. Dados podem estar em formato diferente")
        print("   4. Update pode estar funcionando mas não sendo refletido na view")

if __name__ == "__main__":
    main()
