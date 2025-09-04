#!/usr/bin/env python3
"""
Script para remover duplicações nas tabelas de_para e plano_de_contas
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 REMOVENDO DUPLICAÇÕES NAS TABELAS")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ REMOVENDO DE_PARA DUPLICADOS")
        print("-" * 60)
        
        # Identificar de_para duplicados
        result = conn.execute(text("""
            SELECT 
                descricao_origem,
                COUNT(*) as total,
                MIN(id) as id_manter,
                ARRAY_AGG(id ORDER BY id) as todos_ids
            FROM de_para
            GROUP BY descricao_origem
            HAVING COUNT(*) > 1
            ORDER BY total DESC
        """))
        
        de_para_duplicados = result.fetchall()
        print(f"📊 DE_PARA DUPLICADOS ENCONTRADOS: {len(de_para_duplicados)}")
        
        for row in de_para_duplicados:
            print(f"\n🔍 Processando: {row.descricao_origem}")
            print(f"   Total duplicados: {row.total}")
            print(f"   ID para manter: {row.id_manter}")
            print(f"   IDs para remover: {[id for id in row.todos_ids if id != row.id_manter]}")
            
            # Remover de_para duplicados (manter apenas o primeiro)
            ids_para_remover = [id for id in row.todos_ids if id != row.id_manter]
            
            for id_remover in ids_para_remover:
                try:
                    conn.execute(text("""
                        DELETE FROM de_para WHERE id = :id
                    """), {"id": id_remover})
                    print(f"   ✅ Removido de_para ID: {id_remover}")
                except Exception as e:
                    print(f"   ❌ Erro ao remover de_para ID {id_remover}: {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
        
        print("\n2️⃣ REMOVENDO PLANOS_DE_CONTAS DUPLICADOS")
        print("-" * 60)
        
        # Identificar planos_de_contas duplicados
        result = conn.execute(text("""
            SELECT 
                conta_pai,
                COUNT(*) as total,
                MIN(id) as id_manter,
                ARRAY_AGG(id ORDER BY id) as todos_ids
            FROM plano_de_contas
            GROUP BY conta_pai
            HAVING COUNT(*) > 1
            ORDER BY total DESC
        """))
        
        planos_duplicados = result.fetchall()
        print(f"📊 PLANOS_DE_CONTAS DUPLICADOS ENCONTRADOS: {len(planos_duplicados)}")
        
        for row in planos_duplicados:
            print(f"\n🔍 Processando: {row.conta_pai}")
            print(f"   Total duplicados: {row.total}")
            print(f"   ID para manter: {row.id_manter}")
            print(f"   IDs para remover: {[id for id in row.todos_ids if id != row.id_manter]}")
            
            # Remover planos_de_contas duplicados (manter apenas o primeiro)
            ids_para_remover = [id for id in row.todos_ids if id != row.id_manter]
            
            for id_remover in ids_para_remover:
                try:
                    conn.execute(text("""
                        DELETE FROM plano_de_contas WHERE id = :id
                    """), {"id": id_remover})
                    print(f"   ✅ Removido plano_de_contas ID: {id_remover}")
                except Exception as e:
                    print(f"   ❌ Erro ao remover plano_de_contas ID {id_remover}: {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
        
        print("\n3️⃣ VERIFICANDO RESULTADO")
        print("-" * 60)
        
        # Verificar se ainda há duplicações
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                COUNT(DISTINCT fd.id) as registros_unicos,
                COUNT(*) as registros_totais,
                SUM(fd.valor_original) as valor_total
            FROM financial_data fd
            LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            WHERE fd.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND fd.valor_original IS NOT NULL
            AND dp.descricao_origem IS NOT NULL
            AND pc.conta_pai IS NOT NULL
            AND pc.classificacao_dre_n2 IS NOT NULL
            AND pc.classificacao_dre_n2::text <> ''
            GROUP BY pc.classificacao_dre_n2
            HAVING COUNT(DISTINCT fd.id) <> COUNT(*)
            ORDER BY valor_total DESC
        """))
        
        duplicacoes_restantes = result.fetchall()
        print(f"📊 DUPLICAÇÕES RESTANTES: {len(duplicacoes_restantes)}")
        
        if len(duplicacoes_restantes) == 0:
            print("   ✅ Todas as duplicações foram removidas!")
        else:
            for row in duplicacoes_restantes:
                print(f"   ❌ {row.classificacao_dre_n2}: {row.registros_unicos} únicos, {row.registros_totais} totais")
        
        print("\n4️⃣ TESTANDO VIEW APÓS CORREÇÃO")
        print("-" * 60)
        
        # Testar se a view agora retorna valores corretos
        result = conn.execute(text("""
            SELECT 
                va.descricao,
                SUM(va.valor_total) as valor_total_view
            FROM v_dre_n0_completo va
            WHERE va.empresa_id = '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            AND va.valor_total IS NOT NULL
            AND va.descricao IS NOT NULL
            GROUP BY va.descricao
            ORDER BY valor_total_view DESC
            LIMIT 5
        """))
        
        view_valores = result.fetchall()
        print(f"📊 VALORES NA VIEW APÓS CORREÇÃO:")
        for row in view_valores:
            print(f"   {row.descricao}: R$ {row.valor_total_view:,.2f}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 REMOÇÃO DE DUPLICAÇÕES CONCLUÍDA!")
        print("   • De_para duplicados foram removidos")
        print("   • Planos_de_contas duplicados foram removidos")
        print("   • View deve agora retornar valores corretos")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Testar no frontend para confirmar a correção")
        print("   2. Verificar se os valores do DRE N2 agora batem")
        print("   3. Confirmar que as classificações e nomes continuam funcionando")

if __name__ == "__main__":
    main()
