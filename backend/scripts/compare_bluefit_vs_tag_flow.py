#!/usr/bin/env python3
"""
Script para comparar o fluxo entre Bluefit e TAG para identificar diferenças
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 COMPARANDO FLUXO BLUEFIT vs TAG")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ COMPARANDO ESTRUTURA DE DADOS")
        print("-" * 60)
        
        # Comparar estrutura de dados entre Bluefit e TAG
        empresas = [
            ("2fd835d0-c899-49f4-9096-9fdc3e4d3008", "Bluefit T8"),
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar financial_data
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT classificacao) as classificacoes_unicas,
                    SUM(valor_original) as valor_total,
                    MIN(competencia) as competencia_min,
                    MAX(competencia) as competencia_max
                FROM financial_data
                WHERE empresa_id = :empresa_id
                AND valor_original IS NOT NULL
            """), {"empresa_id": empresa_id})
            
            fd_data = result.fetchone()
            print(f"   Financial Data: {fd_data.total_registros} registros, {fd_data.classificacoes_unicas} classificações")
            print(f"   Valor total: R$ {fd_data.valor_total:,.2f}")
            print(f"   Período: {fd_data.competencia_min} a {fd_data.competencia_max}")
            
            # Verificar de_para
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_mappings,
                    COUNT(DISTINCT descricao_origem) as origens_unicas,
                    COUNT(DISTINCT descricao_destino) as destinos_unicos
                FROM de_para
                WHERE EXISTS (
                    SELECT 1 FROM financial_data fd 
                    WHERE fd.empresa_id = :empresa_id 
                    AND fd.classificacao = de_para.descricao_origem
                )
            """), {"empresa_id": empresa_id})
            
            dp_data = result.fetchone()
            print(f"   De_para: {dp_data.total_mappings} mappings, {dp_data.origens_unicas} origens, {dp_data.destinos_unicos} destinos")
            
            # Verificar plano_de_contas
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_contas,
                    COUNT(CASE WHEN classificacao_dre_n2 IS NOT NULL THEN 1 END) as com_dre_n2,
                    COUNT(CASE WHEN classificacao_dre_n2 IS NULL THEN 1 END) as sem_dre_n2
                FROM plano_de_contas
                WHERE EXISTS (
                    SELECT 1 FROM financial_data fd
                    JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    WHERE fd.empresa_id = :empresa_id
                    AND dp.descricao_destino = plano_de_contas.conta_pai
                )
            """), {"empresa_id": empresa_id})
            
            pc_data = result.fetchone()
            print(f"   Plano Contas: {pc_data.total_contas} contas, {pc_data.com_dre_n2} com DRE N2, {pc_data.sem_dre_n2} sem DRE N2")
        
        print("\n2️⃣ COMPARANDO FLUXO COMPLETO")
        print("-" * 60)
        
        for empresa_id, empresa_nome in empresas:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar fluxo completo
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as registros_fluxo,
                    COUNT(DISTINCT pc.classificacao_dre_n2) as contas_dre_n2,
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
            print(f"   Fluxo Completo: {fluxo_data.registros_fluxo} registros, {fluxo_data.contas_dre_n2} contas DRE N2")
            print(f"   Valor total: R$ {fluxo_data.valor_total_fluxo:,.2f}")
            
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
        
        print("\n3️⃣ VERIFICANDO DIFERENÇAS ESPECÍFICAS")
        print("-" * 60)
        
        # Verificar se há diferenças na estrutura de dados
        print("\n📊 VERIFICANDO ESTRUTURA DE_para:")
        result = conn.execute(text("""
            SELECT 
                e.nome as empresa,
                COUNT(*) as total_mappings,
                COUNT(CASE WHEN dp.descricao_origem IS NULL THEN 1 END) as origens_nulas,
                COUNT(CASE WHEN dp.descricao_destino IS NULL THEN 1 END) as destinos_nulos
            FROM de_para dp
            JOIN empresas e ON dp.empresa_id = e.id
            WHERE e.id = ANY(ARRAY[
                '2fd835d0-c899-49f4-9096-9fdc3e4d3008',
                'd09c3591-3de3-4a8f-913a-2e36de84610f',
                '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            ])
            GROUP BY e.nome
            ORDER BY e.nome
        """))
        
        de_para_structure = result.fetchall()
        for row in de_para_structure:
            print(f"   {row.empresa}: {row.total_mappings} mappings, {row.origens_nulas} origens nulas, {row.destinos_nulos} destinos nulos")
        
        print("\n📊 VERIFICANDO ESTRUTURA PLANO_DE_CONTAS:")
        result = conn.execute(text("""
            SELECT 
                e.nome as empresa,
                COUNT(*) as total_contas,
                COUNT(CASE WHEN pc.classificacao_dre_n2 IS NOT NULL THEN 1 END) as com_dre_n2,
                COUNT(CASE WHEN pc.classificacao_dre_n2 IS NULL THEN 1 END) as sem_dre_n2
            FROM plano_de_contas pc
            JOIN empresas e ON pc.empresa_id = e.id
            WHERE e.id = ANY(ARRAY[
                '2fd835d0-c899-49f4-9096-9fdc3e4d3008',
                'd09c3591-3de3-4a8f-913a-2e36de84610f',
                '7c0c1321-d065-4ed2-afbf-98b2524892ac'
            ])
            GROUP BY e.nome
            ORDER BY e.nome
        """))
        
        plano_structure = result.fetchall()
        for row in plano_structure:
            print(f"   {row.empresa}: {row.total_contas} contas, {row.com_dre_n2} com DRE N2, {row.sem_dre_n2} sem DRE N2")
        
        print("\n4️⃣ VERIFICANDO DRE_STRUCTURE_N2")
        print("-" * 60)
        
        # Verificar se há diferenças no dre_structure_n2
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_contas,
                COUNT(CASE WHEN is_active = true THEN 1 END) as contas_ativas,
                COUNT(CASE WHEN is_active = false THEN 1 END) as contas_inativas
            FROM dre_structure_n2
        """))
        
        dre_n2_data = result.fetchone()
        print(f"📊 DRE_STRUCTURE_N2:")
        print(f"   Total: {dre_n2_data.total_contas} contas")
        print(f"   Ativas: {dre_n2_data.contas_ativas}")
        print(f"   Inativas: {dre_n2_data.contas_inativas}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 ANÁLISE CONCLUÍDA!")
        print("\n💡 POSSÍVEIS DIFERENÇAS:")
        print("   1. Estrutura de dados pode ser diferente entre empresas")
        print("   2. Mapeamentos de_para podem estar incompletos para TAG")
        print("   3. Plano_de_contas pode ter menos contas com DRE N2 para TAG")
        print("   4. DRE_STRUCTURE_N2 pode ter contas inativas que afetam TAG")
        print("   5. View pode ter lógica específica que funciona melhor para Bluefit")

if __name__ == "__main__":
    main()
