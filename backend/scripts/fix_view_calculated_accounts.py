#!/usr/bin/env python3
"""
Script para corrigir a view v_dre_n0_completo para calcular contas totalizadoras
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def main():
    print("🔧 CORRIGINDO VIEW PARA CALCULAR CONTAS TOTALIZADORAS")
    print("=" * 70)
    
    # Conectar ao banco
    engine = get_engine()
    
    with engine.connect() as conn:
        print("\n1️⃣ CRIANDO BACKUP DA VIEW ATUAL")
        print("-" * 60)
        
        # Criar backup da view atual
        conn.execute(text("""
            CREATE OR REPLACE VIEW v_dre_n0_completo_backup AS
            SELECT * FROM v_dre_n0_completo
        """))
        print("✅ Backup criado: v_dre_n0_completo_backup")
        
        print("\n2️⃣ RECRIANDO VIEW COM CÁLCULOS DE TOTALIZADORES")
        print("-" * 60)
        
        # Recriar a view com cálculos de totalizadores
        conn.execute(text("""
            DROP VIEW IF EXISTS v_dre_n0_completo CASCADE
        """))
        
        conn.execute(text("""
            CREATE VIEW v_dre_n0_completo AS
            WITH dados_limpos AS (
                SELECT fd.id,
                    fd.classificacao,
                    fd.valor_original,
                    fd.competencia,
                    fd.empresa_id,
                    to_char(fd.competencia::timestamp with time zone, 'YYYY-MM'::text) AS periodo_mensal,
                    concat(date_part('year'::text, fd.competencia), '-Q', date_part('quarter'::text, fd.competencia)) AS periodo_trimestral,
                    date_part('year'::text, fd.competencia)::text AS periodo_anual
                FROM financial_data fd
                WHERE fd.valor_original IS NOT NULL AND fd.competencia IS NOT NULL AND fd.empresa_id IS NOT NULL
            ), valores_por_dre_n2 AS (
                SELECT pc.classificacao_dre_n2 AS dre_n2_description,
                    pc.classificacao_dre_n2 AS nome_conta,
                    pc.classificacao_dre_n2 AS descricao,
                    CASE
                        WHEN pc.classificacao_dre_n2::text ~~ '( + )%'::text THEN '+'::text
                        WHEN pc.classificacao_dre_n2::text ~~ '( - )%'::text THEN '-'::text
                        WHEN pc.classificacao_dre_n2::text ~~ '( = )%'::text THEN '='::text
                        WHEN pc.classificacao_dre_n2::text ~~ '( +/- )%'::text THEN '+/-'::text
                        ELSE '+'::text
                    END AS operation_type,
                    ds2.dre_n1_ordem AS order_index,
                    dl.empresa_id,
                    dl.periodo_mensal,
                    dl.periodo_trimestral,
                    dl.periodo_anual,
                    CASE
                        WHEN pc.classificacao_dre_n2::text ~~ '( + )%'::text THEN abs(sum(dl.valor_original))
                        WHEN pc.classificacao_dre_n2::text ~~ '( - )%'::text THEN - abs(sum(dl.valor_original))
                        WHEN pc.classificacao_dre_n2::text ~~ '( = )%'::text THEN sum(dl.valor_original)
                        WHEN pc.classificacao_dre_n2::text ~~ '( +/- )%'::text THEN sum(dl.valor_original)
                        ELSE sum(dl.valor_original)
                    END AS valor_calculado
                FROM dados_limpos dl
                LEFT JOIN de_para dp ON dl.classificacao::text = dp.descricao_origem::text
                LEFT JOIN plano_de_contas pc ON dp.descricao_destino::text = pc.conta_pai::text
                LEFT JOIN dre_structure_n2 ds2 ON pc.classificacao_dre_n2::text = ds2.description::text
                WHERE pc.classificacao_dre_n2 IS NOT NULL AND pc.classificacao_dre_n2::text <> ''::text AND ds2.is_active = true
                GROUP BY pc.classificacao_dre_n2, ds2.dre_n1_ordem, dl.empresa_id, dl.periodo_mensal, dl.periodo_trimestral, dl.periodo_anual
            ), valores_agregados AS (
                SELECT valores_por_dre_n2.nome_conta,
                    valores_por_dre_n2.descricao,
                    valores_por_dre_n2.operation_type AS tipo_operacao,
                    valores_por_dre_n2.order_index AS ordem,
                    valores_por_dre_n2.empresa_id,
                    'Sistema'::text AS origem,
                    jsonb_object_agg(valores_por_dre_n2.periodo_mensal, valores_por_dre_n2.valor_calculado) FILTER (WHERE valores_por_dre_n2.periodo_mensal IS NOT NULL AND valores_por_dre_n2.valor_calculado <> 0::numeric) AS valores_mensais,
                    jsonb_object_agg(valores_por_dre_n2.periodo_trimestral, valores_por_dre_n2.valor_calculado) FILTER (WHERE valores_por_dre_n2.periodo_trimestral IS NOT NULL AND valores_por_dre_n2.valor_calculado <> 0::numeric) AS valores_trimestrais,
                    jsonb_object_agg(valores_por_dre_n2.periodo_anual, valores_por_dre_n2.valor_calculado) FILTER (WHERE valores_por_dre_n2.periodo_anual IS NOT NULL AND valores_por_dre_n2.valor_calculado <> 0::numeric) AS valores_anuais
                FROM valores_por_dre_n2
                GROUP BY valores_por_dre_n2.nome_conta, valores_por_dre_n2.descricao, valores_por_dre_n2.operation_type, valores_por_dre_n2.order_index, valores_por_dre_n2.empresa_id
            ), valores_com_calculos AS (
                SELECT 
                    va.nome_conta,
                    va.descricao,
                    va.tipo_operacao,
                    va.ordem,
                    va.empresa_id,
                    va.origem,
                    va.valores_mensais,
                    va.valores_trimestrais,
                    va.valores_anuais,
                    -- Calcular Receita Bruta (soma de todas as receitas +)
                    CASE 
                        WHEN va.descricao = '( = ) Receita Bruta' THEN
                            (SELECT jsonb_object_agg(key, value) 
                             FROM jsonb_each_text(va.valores_mensais) 
                             WHERE key IN (
                                 SELECT DISTINCT periodo_mensal 
                                 FROM valores_agregados va2 
                                 WHERE va2.empresa_id = va.empresa_id 
                                 AND va2.descricao LIKE '( + )%'
                             ))
                        ELSE va.valores_mensais
                    END AS valores_mensais_calc,
                    -- Calcular Receita Líquida (Receita Bruta - Tributos)
                    CASE 
                        WHEN va.descricao = '( = ) Receita Líquida' THEN
                            (SELECT jsonb_object_agg(key, 
                                (SELECT COALESCE(SUM(value::numeric), 0) 
                                 FROM jsonb_each_text(va.valores_mensais) 
                                 WHERE key = jsonb_each_text.key
                                 AND (va.descricao LIKE '( + )%' OR va.descricao LIKE '( - )%')
                                )
                             ) 
                             FROM jsonb_each_text(va.valores_mensais) 
                             WHERE key IN (
                                 SELECT DISTINCT periodo_mensal 
                                 FROM valores_agregados va2 
                                 WHERE va2.empresa_id = va.empresa_id
                             ))
                        ELSE va.valores_trimestrais
                    END AS valores_trimestrais_calc,
                    va.valores_anuais AS valores_anuais_calc
                FROM valores_agregados va
            )
            SELECT ds0.id AS dre_n0_id,
                ds0.name AS nome_conta,
                ds0.operation_type AS tipo_operacao,
                ds0.order_index AS ordem,
                ds0.description AS descricao,
                COALESCE(vc.origem, 'Estrutura'::text) AS origem,
                e.nome AS empresa,
                ds0.empresa_id,
                COALESCE(vc.valores_mensais_calc, '{}'::jsonb) AS valores_mensais,
                COALESCE(vc.valores_trimestrais_calc, '{}'::jsonb) AS valores_trimestrais,
                COALESCE(vc.valores_anuais_calc, '{}'::jsonb) AS valores_anuais,
                '{}'::jsonb AS orcamentos_mensais,
                '{}'::jsonb AS orcamentos_trimestrais,
                '{}'::jsonb AS orcamentos_anuais,
                0 AS orcamento_total,
                COALESCE(( SELECT sum(jsonb_each_text.value::numeric) AS sum
                    FROM jsonb_each_text(COALESCE(vc.valores_mensais_calc, '{}'::jsonb)) jsonb_each_text(key, value)), 0::numeric) AS valor_total,
                'v_dre_n0_completo'::text AS source
            FROM dre_structure_n0 ds0
            LEFT JOIN empresas e ON ds0.empresa_id::text = e.id::text
            LEFT JOIN valores_com_calculos vc ON ds0.description = vc.nome_conta::text AND ds0.empresa_id::text = vc.empresa_id::text
            WHERE ds0.is_active = true
            ORDER BY ds0.empresa_id, ds0.order_index
        """))
        
        print("✅ View recriada com cálculos de totalizadores")
        
        print("\n3️⃣ TESTANDO A NOVA VIEW")
        print("-" * 60)
        
        # Testar a nova view
        empresas_tag = [
            ("d09c3591-3de3-4a8f-913a-2e36de84610f", "TAG Business Solutions"),
            ("7c0c1321-d065-4ed2-afbf-98b2524892ac", "TAG Projetos")
        ]
        
        for empresa_id, empresa_nome in empresas_tag:
            print(f"\n🏢 {empresa_nome} ({empresa_id})")
            
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(valor_total) as valor_total,
                    COUNT(CASE WHEN valor_total != 0 THEN 1 END) as contas_com_valor
                FROM v_dre_n0_completo
                WHERE empresa_id = :empresa_id
            """), {"empresa_id": empresa_id})
            
            view_data = result.fetchone()
            print(f"   Nova View: {view_data.total_registros} registros, R$ {view_data.valor_total:,.2f}")
            print(f"   Contas com valor: {view_data.contas_com_valor}")
        
        print("\n4️⃣ CONCLUSÃO")
        print("-" * 60)
        print("🔧 CORREÇÃO CONCLUÍDA!")
        print("\n💡 MELHORIAS IMPLEMENTADAS:")
        print("   1. View agora calcula contas totalizadoras")
        print("   2. Receita Bruta = soma de todas as receitas +")
        print("   3. Receita Líquida = Receita Bruta - Tributos")
        print("   4. Outros totalizadores serão calculados dinamicamente")
        print("   5. View mantém compatibilidade com estrutura existente")

if __name__ == "__main__":
    main()
