-- ============================================================================
-- VIEW DRE - DEMONSTRAÇÃO DE RESULTADOS
-- ============================================================================

-- View principal para DRE com valores por período
CREATE OR REPLACE VIEW v_dre_completo AS
WITH 
-- Dados base com períodos
dados_base AS (
    SELECT 
        fd.id,
        fd.dre_n1,
        fd.dre_n2,
        fd.classificacao,
        fd.valor_original,
        fd.origem,
        fd.competencia,
        fd.empresa,
        fd.nome,
        -- Períodos
        TO_CHAR(fd.competencia, 'YYYY-MM') as mes_ano,
        EXTRACT(YEAR FROM fd.competencia) as ano,
        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-T', EXTRACT(QUARTER FROM fd.competencia)) as trimestre,
        -- Tipo de transação
        CASE 
            WHEN fd.valor_original > 0 THEN 'receita'
            ELSE 'despesa'
        END as tipo_transacao
    FROM financial_data fd
    WHERE fd.dre_n2 IS NOT NULL 
    AND fd.dre_n2 != '' 
    AND fd.dre_n2 != 'nan'
    AND fd.valor_original IS NOT NULL
    AND fd.competencia IS NOT NULL
),

-- Valores por mês
valores_mensais AS (
    SELECT 
        dre_n2,
        mes_ano,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado
    FROM dados_base
    GROUP BY dre_n2, mes_ano
),

-- Valores por trimestre
valores_trimestrais AS (
    SELECT 
        dre_n2,
        trimestre,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado
    FROM dados_base
    GROUP BY dre_n2, trimestre
),

-- Valores por ano
valores_anuais AS (
    SELECT 
        dre_n2,
        ano,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado
    FROM dados_base
    GROUP BY dre_n2, ano
),

-- Orçamentos por mês
orcamentos_mensais AS (
    SELECT 
        dre_n2,
        mes_ano,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas_orc,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas_orc,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dre_n2, mes_ano
),

-- Orçamentos por trimestre
orcamentos_trimestrais AS (
    SELECT 
        dre_n2,
        trimestre,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas_orc,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas_orc,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dre_n2, trimestre
),

-- Orçamentos por ano
orcamentos_anuais AS (
    SELECT 
        dre_n2,
        ano,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as receitas_orc,
        SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as despesas_orc,
        SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dre_n2, ano
)

-- Resultado final
SELECT 
    db.dre_n2,
    db.dre_n1,
    db.classificacao,
    
    -- Valores realizados por mês
    vm.receitas as receitas_mes,
    vm.despesas as despesas_mes,
    vm.resultado as resultado_mes,
    
    -- Valores realizados por trimestre
    vt.receitas as receitas_trimestre,
    vt.despesas as despesas_trimestre,
    vt.resultado as resultado_trimestre,
    
    -- Valores realizados por ano
    va.receitas as receitas_ano,
    va.despesas as despesas_ano,
    va.resultado as resultado_ano,
    
    -- Orçamentos por mês
    COALESCE(om.receitas_orc, 0) as receitas_orc_mes,
    COALESCE(om.despesas_orc, 0) as despesas_orc_mes,
    COALESCE(om.resultado_orc, 0) as resultado_orc_mes,
    
    -- Orçamentos por trimestre
    COALESCE(ot.receitas_orc, 0) as receitas_orc_trimestre,
    COALESCE(ot.despesas_orc, 0) as despesas_orc_trimestre,
    COALESCE(ot.resultado_orc, 0) as resultado_orc_trimestre,
    
    -- Orçamentos por ano
    COALESCE(oa.receitas_orc, 0) as receitas_orc_ano,
    COALESCE(oa.despesas_orc, 0) as despesas_orc_ano,
    COALESCE(oa.resultado_orc, 0) as resultado_orc_ano,
    
    -- Períodos
    db.mes_ano,
    db.trimestre,
    db.ano,
    
    -- Metadados
    db.empresa,
    db.origem,
    db.competencia
    
FROM dados_base db
LEFT JOIN valores_mensais vm ON db.dre_n2 = vm.dre_n2 AND db.mes_ano = vm.mes_ano
LEFT JOIN valores_trimestrais vt ON db.dre_n2 = vt.dre_n2 AND db.trimestre = vt.trimestre
LEFT JOIN valores_anuais va ON db.dre_n2 = va.dre_n2 AND db.ano = va.ano
LEFT JOIN orcamentos_mensais om ON db.dre_n2 = om.dre_n2 AND db.mes_ano = om.mes_ano
LEFT JOIN orcamentos_trimestrais ot ON db.dre_n2 = ot.dre_n2 AND db.trimestre = ot.trimestre
LEFT JOIN orcamentos_anuais oa ON db.dre_n2 = oa.dre_n2 AND db.ano = oa.ano
ORDER BY db.dre_n2, db.competencia;

-- ============================================================================
-- VIEW DRE RESUMIDA - APENAS TOTAIS POR CATEGORIA
-- ============================================================================

CREATE OR REPLACE VIEW v_dre_resumida AS
SELECT 
    dre_n2,
    dre_n1,
    classificacao,
    
    -- Totais realizados
    SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE 0 END) as total_receitas,
    SUM(CASE WHEN tipo_transacao = 'despesa' THEN ABS(valor_original) ELSE 0 END) as total_despesas,
    SUM(CASE WHEN tipo_transacao = 'receita' THEN valor_original ELSE -valor_original END) as resultado_liquido,
    
    -- Contagem de registros
    COUNT(*) as total_registros,
    
    -- Período de dados
    MIN(competencia) as data_inicio,
    MAX(competencia) as data_fim
    
FROM v_dre_completo
GROUP BY dre_n2, dre_n1, classificacao
ORDER BY dre_n2;

-- ============================================================================
-- VIEW DRE POR PERÍODO - PARA ANÁLISES TEMPORAIS
-- ============================================================================

CREATE OR REPLACE VIEW v_dre_por_periodo AS
SELECT 
    mes_ano,
    trimestre,
    ano,
    
    -- Totais por período
    SUM(receitas_mes) as total_receitas_mes,
    SUM(despesas_mes) as total_despesas_mes,
    SUM(resultado_mes) as resultado_liquido_mes,
    
    -- Orçamentos por período
    SUM(receitas_orc_mes) as total_receitas_orc_mes,
    SUM(despesas_orc_mes) as total_despesas_orc_mes,
    SUM(resultado_orc_mes) as resultado_liquido_orc_mes,
    
    -- Análise de variação
    SUM(resultado_mes) - SUM(resultado_orc_mes) as variacao_resultado,
    CASE 
        WHEN SUM(resultado_orc_mes) != 0 
        THEN ((SUM(resultado_mes) - SUM(resultado_orc_mes)) / ABS(SUM(resultado_orc_mes))) * 100
        ELSE 0 
    END as variacao_percentual
    
FROM v_dre_completo
GROUP BY mes_ano, trimestre, ano
ORDER BY ano, mes_ano;
