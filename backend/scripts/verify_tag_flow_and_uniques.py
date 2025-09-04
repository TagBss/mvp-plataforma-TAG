#!/usr/bin/env python3
"""
Script para verificar se o fluxo está correto para TAG e se os UNIQUEs estão configurados
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 VERIFICANDO FLUXO E UNIQUES PARA TAG")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO ESTRUTURA DAS EMPRESAS")
        print("-" * 60)
        
        # Verificar empresas TAG
        result = conn.execute(text("""
            SELECT 
                id,
                nome,
                grupo_empresa_id,
                COUNT(*) OVER (PARTITION BY grupo_empresa_id) as empresas_no_grupo
            FROM empresas
            WHERE nome LIKE '%TAG%' OR nome LIKE '%tag%'
            ORDER BY grupo_empresa_id, nome
        """))
        
        empresas_tag = result.fetchall()
        print(f"📊 EMPRESAS TAG: {len(empresas_tag)}")
        for row in empresas_tag:
            print(f"   {row.nome} (ID: {row.id})")
            print(f"     Grupo: {row.grupo_empresa_id}")
            print(f"     Empresas no grupo: {row.empresas_no_grupo}")
        
        # Verificar empresas Bluefit
        result = conn.execute(text("""
            SELECT 
                id,
                nome,
                grupo_empresa_id,
                COUNT(*) OVER (PARTITION BY grupo_empresa_id) as empresas_no_grupo
            FROM empresas
            WHERE nome LIKE '%Bluefit%' OR nome LIKE '%bluefit%'
            ORDER BY grupo_empresa_id, nome
        """))
        
        empresas_bluefit = result.fetchall()
        print(f"\n📊 EMPRESAS BLUEFIT: {len(empresas_bluefit)}")
        for row in empresas_bluefit:
            print(f"   {row.nome} (ID: {row.id})")
            print(f"     Grupo: {row.grupo_empresa_id}")
            print(f"     Empresas no grupo: {row.empresas_no_grupo}")
        
        print("\n2️⃣ VERIFICANDO FLUXO FINANCIAL_DATA → DE_PARA → PLANO_DE_CONTAS")
        print("-" * 60)
        
        empresas_tag_ids = [row.id for row in empresas_tag]
        
        for empresa_id in empresas_tag_ids:
            print(f"\n🏢 EMPRESA: {empresa_id}")
            
            # Verificar fluxo completo
            result = conn.execute(text("""
                SELECT 
                    'financial_data' as tabela,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT classificacao) as classificacoes_unicas
                FROM financial_data
                WHERE empresa_id = :empresa_id
                AND valor_original IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    'de_para' as tabela,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT descricao_origem) as classificacoes_unicas
                FROM de_para dp
                WHERE EXISTS (
                    SELECT 1 FROM financial_data fd 
                    WHERE fd.empresa_id = :empresa_id 
                    AND fd.classificacao = dp.descricao_origem
                )
                
                UNION ALL
                
                SELECT 
                    'plano_de_contas' as tabela,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT conta_pai) as classificacoes_unicas
                FROM plano_de_contas pc
                WHERE EXISTS (
                    SELECT 1 FROM financial_data fd
                    JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    WHERE fd.empresa_id = :empresa_id
                    AND dp.descricao_destino = pc.conta_pai
                )
            """), {"empresa_id": empresa_id})
            
            fluxo = result.fetchall()
            for row in fluxo:
                print(f"   {row.tabela}: {row.total_registros} registros, {row.classificacoes_unicas} únicos")
        
        print("\n3️⃣ VERIFICANDO UNIQUES E CONSTRAINTS")
        print("-" * 60)
        
        # Verificar constraints da tabela de_para
        result = conn.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'de_para'
            ORDER BY tc.constraint_name
        """))
        
        constraints_de_para = result.fetchall()
        print(f"📊 CONSTRAINTS DE_PARA: {len(constraints_de_para)}")
        for row in constraints_de_para:
            print(f"   {row.constraint_name}: {row.constraint_type} ({row.column_name})")
        
        # Verificar constraints da tabela plano_de_contas
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
        
        constraints_plano = result.fetchall()
        print(f"\n📊 CONSTRAINTS PLANO_DE_CONTAS: {len(constraints_plano)}")
        for row in constraints_plano:
            print(f"   {row.constraint_name}: {row.constraint_type} ({row.column_name})")
        
        print("\n4️⃣ VERIFICANDO DUPLICAÇÕES POR EMPRESA")
        print("-" * 60)
        
        for empresa_id in empresas_tag_ids:
            print(f"\n🏢 EMPRESA: {empresa_id}")
            
            # Verificar se há classificações duplicadas por empresa
            result = conn.execute(text("""
                SELECT 
                    fd.classificacao,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT dp.id) as de_para_count,
                    COUNT(DISTINCT pc.id) as plano_count,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                GROUP BY fd.classificacao
                HAVING COUNT(DISTINCT dp.id) > 1 OR COUNT(DISTINCT pc.id) > 1
                ORDER BY valor_total DESC
                LIMIT 5
            """), {"empresa_id": empresa_id})
            
            duplicacoes = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM DUPLICAÇÃO: {len(duplicacoes)}")
            for row in duplicacoes:
                print(f"   {row.classificacao}:")
                print(f"     Registros: {row.total_registros}")
                print(f"     De_para: {row.de_para_count}")
                print(f"     Planos: {row.plano_count}")
                print(f"     Valor: R$ {row.valor_total:,.2f}")
        
        print("\n5️⃣ VERIFICANDO DIFERENÇA ENTRE EMPRESAS TAG")
        print("-" * 60)
        
        # Comparar dados entre empresas TAG
        if len(empresas_tag_ids) > 1:
            result = conn.execute(text("""
                SELECT 
                    fd.empresa_id,
                    e.nome as empresa_nome,
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT fd.classificacao) as classificacoes_unicas,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                JOIN empresas e ON fd.empresa_id = e.id
                WHERE fd.empresa_id = ANY(:empresas_ids)
                AND fd.valor_original IS NOT NULL
                GROUP BY fd.empresa_id, e.nome
                ORDER BY valor_total DESC
            """), {"empresas_ids": empresas_tag_ids})
            
            comparacao = result.fetchall()
            print(f"📊 COMPARAÇÃO ENTRE EMPRESAS TAG:")
            for row in comparacao:
                print(f"   {row.empresa_nome}:")
                print(f"     Registros: {row.total_registros}")
                print(f"     Classificações: {row.classificacoes_unicas}")
                print(f"     Valor total: R$ {row.valor_total:,.2f}")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 VERIFICAÇÃO CONCLUÍDA!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Múltiplas empresas TAG podem estar compartilhando dados")
        print("   2. Constraints UNIQUE podem não estar considerando empresa_id")
        print("   3. Fluxo pode estar misturando dados entre empresas")
        print("   4. View pode não estar filtrando corretamente por empresa")

if __name__ == "__main__":
    main()
