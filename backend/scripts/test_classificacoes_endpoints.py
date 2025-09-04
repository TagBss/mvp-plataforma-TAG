#!/usr/bin/env python3
"""
Script para testar os endpoints de classificações
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔍 TESTANDO ENDPOINTS DE CLASSIFICAÇÕES")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ VERIFICANDO DADOS DISPONÍVEIS")
        print("-" * 60)
        
        # Verificar empresas TAG
        empresas_tag = [
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            # Verificar contas DRE N0 disponíveis
            result = conn.execute(text("""
                SELECT 
                    descricao,
                    valor_total
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
                AND valor_total != 0
                ORDER BY valor_total DESC
                LIMIT 5
            """), {"empresa_id": empresa_id})
            
            contas_dre = result.fetchall()
            print(f"   📊 Contas DRE N0 disponíveis: {len(contas_dre)}")
            for row in contas_dre:
                print(f"     {row.descricao}: R$ {row.valor_total:,.2f}")
        
        print("\n2️⃣ TESTANDO ENDPOINT DE CLASSIFICAÇÕES")
        print("-" * 60)
        
        # Testar endpoint de classificações para uma conta específica
        conta_teste = "( + ) Terceirização"
        empresa_teste = "d09c3591-3de3-4a8f-913a-2e36de84610f"
        
        print(f"🔍 Testando classificações para: {conta_teste}")
        print(f"🏢 Empresa: {empresa_teste}")
        
        # Simular a query que o endpoint faria
        result = conn.execute(text("""
            SELECT 
                pc.conta_pai as nome,
                pc.classificacao_dre_n2 as dre_n2_name,
                jsonb_object_agg(
                    to_char(fd.competencia, 'YYYY-MM'), 
                    fd.valor_original
                ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_mensais,
                jsonb_object_agg(
                    concat(date_part('year', fd.competencia), '-Q', date_part('quarter', fd.competencia)), 
                    fd.valor_original
                ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_trimestrais,
                jsonb_object_agg(
                    date_part('year', fd.competencia)::text, 
                    fd.valor_original
                ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_anuais
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
            WHERE fd.empresa_id = :empresa_id
            AND pc.classificacao_dre_n2 = :conta_teste
            AND ds2.is_active = true
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.conta_pai, pc.classificacao_dre_n2
            ORDER BY pc.conta_pai
        """), {"empresa_id": empresa_teste, "conta_teste": conta_teste})
        
        classificacoes = result.fetchall()
        print(f"   📊 Classificações encontradas: {len(classificacoes)}")
        for row in classificacoes:
            print(f"     {row.nome}")
            print(f"       DRE N2: {row.dre_n2_name}")
            print(f"       Valores mensais: {len(row.valores_mensais) if row.valores_mensais else 0} períodos")
            print(f"       Valores trimestrais: {len(row.valores_trimestrais) if row.valores_trimestrais else 0} períodos")
            print(f"       Valores anuais: {len(row.valores_anuais) if row.valores_anuais else 0} períodos")
        
        print("\n3️⃣ TESTANDO ENDPOINT DE NOMES")
        print("-" * 60)
        
        # Testar endpoint de nomes para uma classificação específica
        if classificacoes:
            classificacao_teste = classificacoes[0].nome
            print(f"🔍 Testando nomes para classificação: {classificacao_teste}")
            
            # Simular a query que o endpoint faria
            result = conn.execute(text("""
                SELECT 
                    fd.classificacao as nome,
                    jsonb_object_agg(
                        to_char(fd.competencia, 'YYYY-MM'), 
                        fd.valor_original
                    ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_mensais,
                    jsonb_object_agg(
                        concat(date_part('year', fd.competencia), '-Q', date_part('quarter', fd.competencia)), 
                        fd.valor_original
                    ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_trimestrais,
                    jsonb_object_agg(
                        date_part('year', fd.competencia)::text, 
                        fd.valor_original
                    ) FILTER (WHERE fd.valor_original IS NOT NULL) as valores_anuais
                FROM financial_data fd
                JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                WHERE fd.empresa_id = :empresa_id
                AND pc.classificacao_dre_n2 = :conta_teste
                AND pc.conta_pai = :classificacao_teste
                AND ds2.is_active = true
                AND fd.valor_original IS NOT NULL
                GROUP BY fd.classificacao
                ORDER BY fd.classificacao
            """), {
                "empresa_id": empresa_teste, 
                "conta_teste": conta_teste,
                "classificacao_teste": classificacao_teste
            })
            
            nomes = result.fetchall()
            print(f"   📊 Nomes encontrados: {len(nomes)}")
            for row in nomes:
                print(f"     {row.nome}")
                print(f"       Valores mensais: {len(row.valores_mensais) if row.valores_mensais else 0} períodos")
                print(f"       Valores trimestrais: {len(row.valores_trimestrais) if row.valores_trimestrais else 0} períodos")
                print(f"       Valores anuais: {len(row.valores_anuais) if row.valores_anuais else 0} períodos")
        
        print("\n4️⃣ VERIFICANDO ESTRUTURA DOS DADOS")
        print("-" * 60)
        
        # Verificar se há dados suficientes para expansão
        result = conn.execute(text("""
            SELECT 
                pc.classificacao_dre_n2,
                COUNT(DISTINCT pc.conta_pai) as total_classificacoes,
                COUNT(DISTINCT fd.classificacao) as total_nomes
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
            JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
            WHERE fd.empresa_id = :empresa_id
            AND ds2.is_active = true
            AND fd.valor_original IS NOT NULL
            GROUP BY pc.classificacao_dre_n2
            ORDER BY total_classificacoes DESC
        """), {"empresa_id": empresa_teste})
        
        estrutura = result.fetchall()
        print(f"📊 ESTRUTURA DOS DADOS:")
        for row in estrutura:
            print(f"   {row.classificacao_dre_n2}")
            print(f"     Classificações: {row.total_classificacoes}")
            print(f"     Nomes: {row.total_nomes}")
        
        print("\n5️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔍 TESTE CONCLUÍDO!")
        print("\n💡 POSSÍVEIS PROBLEMAS:")
        print("   1. Endpoints podem não estar retornando dados no formato esperado")
        print("   2. Frontend pode não estar processando a resposta corretamente")
        print("   3. Cache pode estar interferindo na expansão")
        print("   4. Lógica de expansão pode ter bugs")

if __name__ == "__main__":
    main()
