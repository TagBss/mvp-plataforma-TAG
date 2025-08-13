-- ============================================================================
-- VIEW DFC - DEMONSTRAÇÃO DE FLUXO DE CAIXA
-- ============================================================================

-- View principal para DFC com valores por período
CREATE OR REPLACE VIEW v_dfc_completo AS
WITH 
-- Dados base com períodos
dados_base AS (
    SELECT 
        fd.id,
        fd.dfc_n1,
        fd.dfc_n2,
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
            WHEN fd.valor_original > 0 THEN 'entrada'
            ELSE 'saida'
        END as tipo_transacao
    FROM financial_data fd
    WHERE fd.dfc_n2 IS NOT NULL 
    AND fd.dfc_n2 != '' 
    AND fd.dfc_n2 != 'nan'
    AND fd.valor_original IS NOT NULL
    AND fd.competencia IS NOT NULL
),

-- Valores por mês
valores_mensais AS (
    SELECT 
        dfc_n2,
        mes_ano,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido
    FROM dados_base
    GROUP BY dfc_n2, mes_ano
),

-- Valores por trimestre
valores_trimestrais AS (
    SELECT 
        dfc_n2,
        trimestre,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido
    FROM dados_base
    GROUP BY dfc_n2, trimestre
),

-- Valores por ano
valores_anuais AS (
    SELECT 
        dfc_n2,
        ano,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido
    FROM dados_base
    GROUP BY dfc_n2, ano
),

-- Orçamentos por mês
orcamentos_mensais AS (
    SELECT 
        dfc_n2,
        mes_ano,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas_orc,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas_orc,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dfc_n2, mes_ano
),

-- Orçamentos por trimestre
orcamentos_trimestrais AS (
    SELECT 
        dfc_n2,
        trimestre,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas_orc,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas_orc,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dfc_n2, trimestre
),

-- Orçamentos por ano
orcamentos_anuais AS (
    SELECT 
        dfc_n2,
        ano,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as entradas_orc,
        SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as saidas_orc,
        SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido_orc
    FROM dados_base
    WHERE origem = 'ORC'
    GROUP BY dfc_n2, ano
)

-- Resultado final
SELECT 
    db.dfc_n2,
    db.dfc_n1,
    db.classificacao,
    
    -- Valores realizados por mês
    vm.entradas as entradas_mes,
    vm.saidas as saidas_mes,
    vm.fluxo_liquido as fluxo_liquido_mes,
    
    -- Valores realizados por trimestre
    vt.entradas as entradas_trimestre,
    vt.saidas as saidas_trimestre,
    vt.fluxo_liquido as fluxo_liquido_trimestre,
    
    -- Valores realizados por ano
    va.entradas as entradas_ano,
    va.saidas as saidas_ano,
    va.fluxo_liquido as fluxo_liquido_ano,
    
    -- Orçamentos por mês
    COALESCE(om.entradas_orc, 0) as entradas_orc_mes,
    COALESCE(om.saidas_orc, 0) as saidas_orc_mes,
    COALESCE(om.fluxo_liquido_orc, 0) as fluxo_liquido_orc_mes,
    
    -- Orçamentos por trimestre
    COALESCE(ot.entradas_orc, 0) as entradas_orc_trimestre,
    COALESCE(ot.saidas_orc, 0) as saidas_orc_trimestre,
    COALESCE(ot.fluxo_liquido_orc, 0) as fluxo_liquido_orc_trimestre,
    
    -- Orçamentos por ano
    COALESCE(oa.entradas_orc, 0) as entradas_orc_ano,
    COALESCE(oa.saidas_orc, 0) as saidas_orc_ano,
    COALESCE(oa.fluxo_liquido_orc, 0) as fluxo_liquido_orc_ano,
    
    -- Períodos
    db.mes_ano,
    db.trimestre,
    db.ano,
    
    -- Metadados
    db.empresa,
    db.origem,
    db.competencia
    
FROM dados_base db
LEFT JOIN valores_mensais vm ON db.dfc_n2 = vm.dfc_n2 AND db.mes_ano = vm.mes_ano
LEFT JOIN valores_trimestrais vt ON db.dfc_n2 = vt.dfc_n2 AND db.trimestre = vt.trimestre
LEFT JOIN valores_anuais va ON db.dfc_n2 = va.dfc_n2 AND db.ano = va.ano
LEFT JOIN orcamentos_mensais om ON db.dfc_n2 = om.dfc_n2 AND db.mes_ano = om.mes_ano
LEFT JOIN orcamentos_trimestrais ot ON db.dfc_n2 = ot.dfc_n2 AND db.trimestre = ot.trimestre
LEFT JOIN orcamentos_anuais oa ON db.dfc_n2 = oa.dfc_n2 AND db.ano = oa.ano
ORDER BY db.dfc_n2, db.competencia;

-- ============================================================================
-- VIEW DFC RESUMIDA - APENAS TOTAIS POR CATEGORIA
-- ============================================================================

CREATE OR REPLACE VIEW v_dfc_resumida AS
SELECT 
    dfc_n2,
    dfc_n1,
    classificacao,
    
    -- Totais realizados
    SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE 0 END) as total_entradas,
    SUM(CASE WHEN tipo_transacao = 'saida' THEN ABS(valor_original) ELSE 0 END) as total_saidas,
    SUM(CASE WHEN tipo_transacao = 'entrada' THEN valor_original ELSE -valor_original END) as fluxo_liquido_total,
    
    -- Contagem de registros
    COUNT(*) as total_registros,
    
    -- Período de dados
    MIN(competencia) as data_inicio,
    MAX(competencia) as data_fim
    
FROM v_dfc_completo
GROUP BY dfc_n2, dfc_n1, classificacao
ORDER BY dfc_n2;

-- ============================================================================
-- VIEW DFC POR PERÍODO - PARA ANÁLISES TEMPORAIS
-- ============================================================================

CREATE OR REPLACE VIEW v_dfc_por_periodo AS
SELECT 
    mes_ano,
    trimestre,
    ano,
    
    -- Totais por período
    SUM(entradas_mes) as total_entradas_mes,
    SUM(saidas_mes) as total_saidas_mes,
    SUM(fluxo_liquido_mes) as fluxo_liquido_mes,
    
    -- Orçamentos por período
    SUM(entradas_orc_mes) as total_entradas_orc_mes,
    SUM(saidas_orc_mes) as total_saidas_orc_mes,
    SUM(fluxo_liquido_orc_mes) as fluxo_liquido_orc_mes,
    
    -- Análise de variação
    SUM(fluxo_liquido_mes) - SUM(fluxo_liquido_orc_mes) as variacao_fluxo,
    CASE 
        WHEN SUM(fluxo_liquido_orc_mes) != 0 
        THEN ((SUM(fluxo_liquido_mes) - SUM(fluxo_liquido_orc_mes)) / ABS(SUM(fluxo_liquido_orc_mes))) * 100
        ELSE 0 
    END as variacao_percentual
    
FROM v_dfc_completo
GROUP BY mes_ano, trimestre, ano
ORDER BY ano, mes_ano;

-- ============================================================================
-- VIEW DFC SALDO ACUMULADO - PARA CÁLCULO DE SALDO INICIAL
-- ============================================================================

CREATE OR REPLACE VIEW v_dfc_saldo_acumulado AS
WITH saldos_por_mes AS (
    SELECT 
        mes_ano,
        SUM(fluxo_liquido_mes) as fluxo_mes
    FROM v_dfc_completo
    GROUP BY mes_ano
    ORDER BY mes_ano
)
SELECT 
    mes_ano,
    fluxo_mes,
    SUM(fluxo_mes) OVER (ORDER BY mes_ano ROWS UNBOUNDED PRECEDING) as saldo_acumulado
FROM saldos_por_mes
ORDER BY mes_ano;
