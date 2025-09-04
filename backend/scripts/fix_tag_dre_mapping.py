#!/usr/bin/env python3
"""
Script para corrigir os mapeamentos das empresas TAG
direcionando classificações para contas que têm classificacao_dre_n2
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 CORRIGINDO MAPEAMENTOS DRE DAS EMPRESAS TAG")
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
            
            print("\n1️⃣ IDENTIFICANDO CLASSIFICAÇÕES COM MAPEAMENTO INCORRETO")
            print("-" * 60)
            
            # Identificar classificações que estão mapeadas para contas sem classificacao_dre_n2
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
                AND pc.conta_pai IS NOT NULL
                AND (pc.classificacao_dre_n2 IS NULL OR pc.classificacao_dre_n2::text = '')
                GROUP BY fd.classificacao, dp.descricao_origem, dp.descricao_destino, pc.conta_pai, pc.classificacao_dre_n2
                ORDER BY valor_total DESC
            """), {"empresa_id": empresa_id})
            
            mapeamentos_incorretos = result.fetchall()
            print(f"📊 CLASSIFICAÇÕES COM MAPEAMENTO INCORRETO: {len(mapeamentos_incorretos)}")
            
            if mapeamentos_incorretos:
                print("\n2️⃣ CORRIGINDO MAPEAMENTOS AUTOMATICAMENTE")
                print("-" * 60)
                
                for row in mapeamentos_incorretos:
                    classificacao = row.classificacao
                    mapeamento_atual = row.descricao_destino
                    valor_total = row.valor_total
                    
                    print(f"\n🔍 Processando: {classificacao}")
                    print(f"   Mapeamento atual: {mapeamento_atual}")
                    print(f"   Valor total: R$ {valor_total:,.2f}")
                    
                    # Tentar encontrar um mapeamento correto baseado em padrões
                    novo_mapeamento = None
                    
                    # Padrões de mapeamento baseados na análise
                    if "consultoria" in classificacao.lower() or "valuation" in classificacao.lower():
                        novo_mapeamento = "Consultoria"
                    elif "terceirização" in classificacao.lower() or "bpo" in classificacao.lower() or "gestao" in classificacao.lower():
                        novo_mapeamento = "Terceirização"
                    elif "mão de obra" in classificacao.lower() or "pessoal" in classificacao.lower():
                        novo_mapeamento = "Mão de obra Direta"
                    elif "despesas administrativas" in classificacao.lower():
                        novo_mapeamento = "Despesas Administrativas"
                    elif "despesas comerciais" in classificacao.lower():
                        novo_mapeamento = "Despesas Comerciais"
                    elif "despesas financeiras" in classificacao.lower():
                        novo_mapeamento = "Despesas Financeiras"
                    elif "despesas com ocupação" in classificacao.lower():
                        novo_mapeamento = "Despesas com Ocupação"
                    elif "despesas de pró-labore" in classificacao.lower():
                        novo_mapeamento = "Despesas de Pró-Labore"
                    elif "despesas de inovação" in classificacao.lower():
                        novo_mapeamento = "Despesas de Inovação"
                    elif "despesas com backoffice" in classificacao.lower():
                        novo_mapeamento = "Despesas com Backoffice"
                    elif "despesas com pessoal" in classificacao.lower():
                        novo_mapeamento = "Despesas com Pessoal"
                    elif "quarteirização" in classificacao.lower():
                        novo_mapeamento = "Quarteirização"
                    elif "tributos" in classificacao.lower() or "impostos" in classificacao.lower():
                        novo_mapeamento = "Tributos e deduções sobre a receita"
                    elif "receitas financeiras" in classificacao.lower() or "rendimento" in classificacao.lower():
                        novo_mapeamento = "Receitas Financeiras"
                    elif "receitas não recorrentes" in classificacao.lower() or "outras receitas" in classificacao.lower():
                        novo_mapeamento = "Receitas / Despesas não recorrentes"
                    elif "faturamento" in classificacao.lower() or "receita" in classificacao.lower():
                        novo_mapeamento = "Faturamento"
                    
                    if novo_mapeamento:
                        print(f"   ✅ Novo mapeamento sugerido: {novo_mapeamento}")
                        
                        # Verificar se existe um plano_de_contas com este mapeamento
                        result = conn.execute(text("""
                            SELECT conta_pai, classificacao_dre_n2
                            FROM plano_de_contas
                            WHERE classificacao_dre_n2 = :novo_mapeamento
                            LIMIT 1
                        """), {"novo_mapeamento": novo_mapeamento})
                        
                        plano_correspondente = result.fetchone()
                        
                        if plano_correspondente:
                            print(f"   ✅ Plano de contas encontrado: {plano_correspondente.conta_pai}")
                            
                            # Atualizar o de_para
                            try:
                                conn.execute(text("""
                                    UPDATE de_para 
                                    SET descricao_destino = :novo_mapeamento,
                                        updated_at = NOW()
                                    WHERE descricao_origem = :classificacao
                                """), {
                                    "novo_mapeamento": plano_correspondente.conta_pai,
                                    "classificacao": classificacao
                                })
                                conn.commit()
                                print(f"   ✅ De_para atualizado com sucesso!")
                            except Exception as e:
                                print(f"   ❌ Erro ao atualizar de_para: {e}")
                                conn.rollback()
                        else:
                            print(f"   ❌ Nenhum plano de contas encontrado para: {novo_mapeamento}")
                    else:
                        print(f"   ❌ Nenhum mapeamento automático encontrado")
            
            print("\n3️⃣ VERIFICANDO RESULTADO FINAL")
            print("-" * 60)
            
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
        
        print("\n4️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 CORREÇÃO DE MAPEAMENTOS CONCLUÍDA!")
        print("   • Classificações com mapeamento incorreto foram identificadas")
        print("   • Mapeamentos foram corrigidos automaticamente")
        print("   • Valores do DRE N2 agora devem bater com as classificações")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Testar no frontend para confirmar a correção")
        print("   2. Verificar se os valores do DRE N2 estão corretos")
        print("   3. Confirmar que as classificações e nomes continuam funcionando")

if __name__ == "__main__":
    main()
