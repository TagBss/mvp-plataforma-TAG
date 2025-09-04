#!/usr/bin/env python3
"""
Script para mapear automaticamente as classificações faltantes das empresas TAG
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 MAPEANDO CLASSIFICAÇÕES FALTANTES DAS EMPRESAS TAG")
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
            
            print("\n1️⃣ IDENTIFICANDO CLASSIFICAÇÕES SEM MAPEAMENTO")
            print("-" * 60)
            
            # Identificar classificações que não têm mapeamento
            result = conn.execute(text("""
                SELECT DISTINCT
                    fd.classificacao,
                    COUNT(*) as total_registros,
                    SUM(fd.valor_original) as valor_total
                FROM financial_data fd
                LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                WHERE fd.empresa_id = :empresa_id
                AND fd.valor_original IS NOT NULL
                AND (dp.descricao_origem IS NULL OR dp.descricao_origem::text = '')
                GROUP BY fd.classificacao
                ORDER BY valor_total DESC
            """), {"empresa_id": empresa_id})
            
            sem_mapeamento = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES SEM MAPEAMENTO: {len(sem_mapeamento)}")
            
            if sem_mapeamento:
                print("\n2️⃣ MAPEANDO CLASSIFICAÇÕES AUTOMATICAMENTE")
                print("-" * 60)
                
                for row in sem_mapeamento:
                    classificacao = row.classificacao
                    valor_total = row.valor_total
                    
                    print(f"\n🔍 Processando: {classificacao}")
                    print(f"   Valor total: R$ {valor_total:,.2f}")
                    
                    # Tentar mapear automaticamente baseado em padrões
                    mapeamento_encontrado = None
                    
                    # Padrões de mapeamento baseados na análise anterior
                    if "consultoria" in classificacao.lower():
                        mapeamento_encontrado = "Consultoria"
                    elif "terceirização" in classificacao.lower() or "bpo" in classificacao.lower():
                        mapeamento_encontrado = "Terceirização"
                    elif "mão de obra" in classificacao.lower() or "pessoal" in classificacao.lower():
                        mapeamento_encontrado = "Mão de obra Direta"
                    elif "despesas administrativas" in classificacao.lower():
                        mapeamento_encontrado = "Despesas Administrativas"
                    elif "despesas comerciais" in classificacao.lower():
                        mapeamento_encontrado = "Despesas Comerciais"
                    elif "despesas financeiras" in classificacao.lower():
                        mapeamento_encontrado = "Despesas Financeiras"
                    elif "despesas com ocupação" in classificacao.lower():
                        mapeamento_encontrado = "Despesas com Ocupação"
                    elif "despesas de pró-labore" in classificacao.lower():
                        mapeamento_encontrado = "Despesas de Pró-Labore"
                    elif "despesas de inovação" in classificacao.lower():
                        mapeamento_encontrado = "Despesas de Inovação"
                    elif "despesas com backoffice" in classificacao.lower():
                        mapeamento_encontrado = "Despesas com Backoffice"
                    elif "despesas com pessoal" in classificacao.lower():
                        mapeamento_encontrado = "Despesas com Pessoal"
                    elif "quarteirização" in classificacao.lower():
                        mapeamento_encontrado = "Quarteirização"
                    elif "tributos" in classificacao.lower() or "impostos" in classificacao.lower():
                        mapeamento_encontrado = "Tributos e deduções sobre a receita"
                    elif "receitas financeiras" in classificacao.lower():
                        mapeamento_encontrado = "Receitas Financeiras"
                    elif "receitas não recorrentes" in classificacao.lower():
                        mapeamento_encontrado = "Receitas / Despesas não recorrentes"
                    
                    if mapeamento_encontrado:
                        print(f"   ✅ Mapeamento encontrado: {mapeamento_encontrado}")
                        
                        # Verificar se já existe um de_para para esta classificacao
                        result = conn.execute(text("""
                            SELECT id FROM de_para 
                            WHERE descricao_origem = :classificacao
                        """), {"classificacao": classificacao})
                        
                        de_para_existente = result.fetchone()
                        
                        if de_para_existente:
                            print(f"   ⚠️  Já existe de_para para esta classificacao")
                        else:
                            # Criar novo de_para
                            try:
                                conn.execute(text("""
                                    INSERT INTO de_para (descricao_origem, descricao_destino, created_at, updated_at)
                                    VALUES (:classificacao, :mapeamento, NOW(), NOW())
                                """), {
                                    "classificacao": classificacao,
                                    "mapeamento": mapeamento_encontrado
                                })
                                conn.commit()
                                print(f"   ✅ De_para criado com sucesso!")
                            except Exception as e:
                                print(f"   ❌ Erro ao criar de_para: {e}")
                                conn.rollback()
                    else:
                        print(f"   ❌ Nenhum mapeamento automático encontrado")
            
            print("\n3️⃣ VERIFICANDO MAPEAMENTOS INCOMPLETOS")
            print("-" * 60)
            
            # Verificar classificações que têm mapeamento mas não chegam ao plano_de_contas
            result = conn.execute(text("""
                SELECT DISTINCT
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
                AND (pc.conta_pai IS NULL OR pc.classificacao_dre_n2 IS NULL)
                GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
                ORDER BY valor_total DESC
                LIMIT 10
            """), {"empresa_id": empresa_id})
            
            mapeamento_incompleto = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM MAPEAMENTO INCOMPLETO: {len(mapeamento_incompleto)}")
            
            if mapeamento_incompleto:
                print("\n4️⃣ COMPLETANDO MAPEAMENTOS INCOMPLETOS")
                print("-" * 60)
                
                for row in mapeamento_incompleto:
                    classificacao = row.classificacao
                    descricao_destino = row.descricao_destino
                    valor_total = row.valor_total
                    
                    print(f"\n🔍 Processando: {classificacao}")
                    print(f"   Mapeamento atual: {descricao_destino}")
                    print(f"   Valor total: R$ {valor_total:,.2f}")
                    
                    # Tentar encontrar um plano_de_contas correspondente
                    result = conn.execute(text("""
                        SELECT conta_pai, classificacao_dre_n2
                        FROM plano_de_contas
                        WHERE conta_pai = :descricao_destino
                        AND classificacao_dre_n2 IS NOT NULL
                        AND classificacao_dre_n2::text <> ''
                        LIMIT 1
                    """), {"descricao_destino": descricao_destino})
                    
                    plano_correspondente = result.fetchone()
                    
                    if plano_correspondente:
                        print(f"   ✅ Plano de contas encontrado: {plano_correspondente.conta_pai} → {plano_correspondente.classificacao_dre_n2}")
                    else:
                        print(f"   ❌ Nenhum plano de contas correspondente encontrado")
        
        print("\n5️⃣ VERIFICANDO RESULTADO FINAL")
        print("-" * 60)
        
        for empresa_id in empresas_tag:
            print(f"\n🏢 EMPRESA: {empresa_id}")
            
            # Verificar diferença entre DRE N2 e classificações após correção
            result = conn.execute(text("""
                WITH dre_n2_totais AS (
                    SELECT 
                        pc.classificacao_dre_n2,
                        SUM(fd.valor_original) as valor_total_dre_n2
                    FROM financial_data fd
                    LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND pc.classificacao_dre_n2::text <> ''
                    GROUP BY pc.classificacao_dre_n2
                ),
                classificacoes_totais AS (
                    SELECT 
                        pc.classificacao_dre_n2,
                        SUM(fd.valor_original) as valor_total_classificacoes
                    FROM financial_data fd
                    LEFT JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                    LEFT JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                    LEFT JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2 = ds2.description
                    WHERE fd.empresa_id = :empresa_id
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND pc.classificacao_dre_n2::text <> ''
                    AND ds2.is_active = true
                    GROUP BY pc.classificacao_dre_n2
                )
                SELECT 
                    COALESCE(dn2.classificacao_dre_n2, cl.classificacao_dre_n2) as classificacao,
                    dn2.valor_total_dre_n2,
                    cl.valor_total_classificacoes,
                    COALESCE(dn2.valor_total_dre_n2, 0) - COALESCE(cl.valor_total_classificacoes, 0) as diferenca
                FROM dre_n2_totais dn2
                FULL OUTER JOIN classificacoes_totais cl ON dn2.classificacao_dre_n2 = cl.classificacao_dre_n2
                WHERE COALESCE(dn2.valor_total_dre_n2, 0) <> COALESCE(cl.valor_total_classificacoes, 0)
                ORDER BY ABS(COALESCE(dn2.valor_total_dre_n2, 0) - COALESCE(cl.valor_total_classificacoes, 0)) DESC
            """), {"empresa_id": empresa_id})
            
            diferencas = result.fetchall()
            print(f"📊 DIFERENÇAS RESTANTES: {len(diferencas)}")
            
            if len(diferencas) == 0:
                print("   ✅ Todas as diferenças foram resolvidas!")
            else:
                for row in diferencas:
                    print(f"   {row.classificacao}: Diferença de R$ {row.diferenca:,.2f}")
        
        print("\n6️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 MAPEAMENTO AUTOMÁTICO CONCLUÍDO!")
        print("   • Classificações sem mapeamento foram identificadas")
        print("   • Mapeamentos automáticos foram aplicados")
        print("   • Mapeamentos incompletos foram verificados")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Verificar se os valores do DRE N2 agora batem com as classificações")
        print("   2. Testar no frontend para confirmar a correção")
        print("   3. Ajustar mapeamentos manuais se necessário")

if __name__ == "__main__":
    main()
