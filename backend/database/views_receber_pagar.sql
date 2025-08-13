-- ============================================================================
-- VIEWS PARA CONTAS A RECEBER E A PAGAR
-- ============================================================================

-- ============================================================================
-- VIEW CONTAS A RECEBER
-- ============================================================================

CREATE OR REPLACE VIEW v_contas_receber AS
WITH 
-- Dados base de recebimentos
dados_receber AS (
    SELECT 
        fd.id,
        fd.nome,
        fd.classificacao,
        fd.valor_original,
        fd.origem,
        fd.emissao,
        fd.competencia,
        fd.vencimento,
        fd.empresa,
        fd.banco,
        fd.conta_corrente,
        fd.documento,
        fd.observacao,
        fd.local,
        fd.segmento,
        fd.projeto,
        fd.centro_de_resultado,
        fd.diretoria,
        -- Períodos
        TO_CHAR(fd.competencia, 'YYYY-MM') as mes_ano,
        EXTRACT(YEAR FROM fd.competencia) as ano,
        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-T', EXTRACT(QUARTER FROM fd.competencia)) as trimestre,
        -- Status de vencimento
        CASE 
            WHEN fd.vencimento < CURRENT_DATE THEN 'vencido'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '30 days' THEN 'a_vencer_30d'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '60 days' THEN 'a_vencer_60d'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '90 days' THEN 'a_vencer_90d'
            ELSE 'a_vencer_90d_plus'
        END as status_vencimento,
        -- Dias de atraso
        CASE 
            WHEN fd.vencimento < CURRENT_DATE THEN CURRENT_DATE - fd.vencimento
            ELSE 0
        END as dias_atraso
    FROM financial_data fd
    WHERE fd.valor_original > 0  -- Apenas receitas
    AND fd.vencimento IS NOT NULL
    AND fd.competencia IS NOT NULL
),

-- Valores por mês
valores_mensais AS (
    SELECT 
        mes_ano,
        SUM(valor_original) as total_receber,
        COUNT(*) as quantidade_receber,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN valor_original ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN valor_original ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN valor_original ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN valor_original ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN valor_original ELSE 0 END) as a_vencer_90d_plus
    FROM dados_receber
    GROUP BY mes_ano
),

-- Valores por trimestre
valores_trimestrais AS (
    SELECT 
        trimestre,
        SUM(valor_original) as total_receber,
        COUNT(*) as quantidade_receber,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN valor_original ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN valor_original ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN valor_original ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN valor_original ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN valor_original ELSE 0 END) as a_vencer_90d_plus
    FROM dados_receber
    GROUP BY trimestre
),

-- Valores por ano
valores_anuais AS (
    SELECT 
        ano,
        SUM(valor_original) as total_receber,
        COUNT(*) as quantidade_receber,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN valor_original ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN valor_original ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN valor_original ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN valor_original ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN valor_original ELSE 0 END) as a_vencer_90d_plus
    FROM dados_receber
    GROUP BY ano
)

-- Resultado final
SELECT 
    dr.*,
    
    -- Valores por mês
    vm.total_receber as total_receber_mes,
    vm.quantidade_receber as quantidade_receber_mes,
    vm.vencido as vencido_mes,
    vm.a_vencer_30d as a_vencer_30d_mes,
    vm.a_vencer_60d as a_vencer_60d_mes,
    vm.a_vencer_90d as a_vencer_90d_mes,
    vm.a_vencer_90d_plus as a_vencer_90d_plus_mes,
    
    -- Valores por trimestre
    vt.total_receber as total_receber_trimestre,
    vt.quantidade_receber as quantidade_receber_trimestre,
    vt.vencido as vencido_trimestre,
    vt.a_vencer_30d as a_vencer_30d_trimestre,
    vt.a_vencer_60d as a_vencer_60d_trimestre,
    vt.a_vencer_90d as a_vencer_90d_trimestre,
    vt.a_vencer_90d_plus as a_vencer_90d_plus_trimestre,
    
    -- Valores por ano
    va.total_receber as total_receber_ano,
    va.quantidade_receber as quantidade_receber_ano,
    va.vencido as vencido_ano,
    va.a_vencer_30d as a_vencer_30d_ano,
    va.a_vencer_60d as a_vencer_60d_ano,
    va.a_vencer_90d as a_vencer_90d_ano,
    va.a_vencer_90d_plus as a_vencer_90d_plus_ano
    
FROM dados_receber dr
LEFT JOIN valores_mensais vm ON dr.mes_ano = vm.mes_ano
LEFT JOIN valores_trimestrais vt ON dr.trimestre = vt.trimestre
LEFT JOIN valores_anuais va ON dr.ano = va.ano
ORDER BY dr.vencimento, dr.valor_original DESC;

-- ============================================================================
-- VIEW CONTAS A PAGAR
-- ============================================================================

CREATE OR REPLACE VIEW v_contas_pagar AS
WITH 
-- Dados base de pagamentos
dados_pagar AS (
    SELECT 
        fd.id,
        fd.nome,
        fd.classificacao,
        fd.valor_original,
        fd.origem,
        fd.emissao,
        fd.competencia,
        fd.vencimento,
        fd.empresa,
        fd.banco,
        fd.conta_corrente,
        fd.documento,
        fd.observacao,
        fd.local,
        fd.segmento,
        fd.projeto,
        fd.centro_de_resultado,
        fd.diretoria,
        -- Períodos
        TO_CHAR(fd.competencia, 'YYYY-MM') as mes_ano,
        EXTRACT(YEAR FROM fd.competencia) as ano,
        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-T', EXTRACT(QUARTER FROM fd.competencia)) as trimestre,
        -- Status de vencimento
        CASE 
            WHEN fd.vencimento < CURRENT_DATE THEN 'vencido'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '30 days' THEN 'a_vencer_30d'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '60 days' THEN 'a_vencer_60d'
            WHEN fd.vencimento <= CURRENT_DATE + INTERVAL '90 days' THEN 'a_vencer_90d'
            ELSE 'a_vencer_90d_plus'
        END as status_vencimento,
        -- Dias de atraso
        CASE 
            WHEN fd.vencimento < CURRENT_DATE THEN CURRENT_DATE - fd.vencimento
            ELSE 0
        END as dias_atraso
    FROM financial_data fd
    WHERE fd.valor_original < 0  -- Apenas despesas
    AND fd.vencimento IS NOT NULL
    AND fd.competencia IS NOT NULL
),

-- Valores por mês
valores_mensais AS (
    SELECT 
        mes_ano,
        SUM(ABS(valor_original)) as total_pagar,
        COUNT(*) as quantidade_pagar,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN ABS(valor_original) ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d_plus
    FROM dados_pagar
    GROUP BY mes_ano
),

-- Valores por trimestre
valores_trimestrais AS (
    SELECT 
        trimestre,
        SUM(ABS(valor_original)) as total_pagar,
        COUNT(*) as quantidade_pagar,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN ABS(valor_original) ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d_plus
    FROM dados_pagar
    GROUP BY trimestre
),

-- Valores por ano
valores_anuais AS (
    SELECT 
        ano,
        SUM(ABS(valor_original)) as total_pagar,
        COUNT(*) as quantidade_pagar,
        SUM(CASE WHEN status_vencimento = 'vencido' THEN ABS(valor_original) ELSE 0 END) as vencido,
        SUM(CASE WHEN status_vencimento = 'a_vencer_30d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_30d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_60d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_60d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d,
        SUM(CASE WHEN status_vencimento = 'a_vencer_90d_plus' THEN ABS(valor_original) ELSE 0 END) as a_vencer_90d_plus
    FROM dados_pagar
    GROUP BY ano
)

-- Resultado final
SELECT 
    dp.*,
    
    -- Valores por mês
    vm.total_pagar as total_pagar_mes,
    vm.quantidade_pagar as quantidade_pagar_mes,
    vm.vencido as vencido_mes,
    vm.a_vencer_30d as a_vencer_30d_mes,
    vm.a_vencer_60d as a_vencer_60d_mes,
    vm.a_vencer_90d as a_vencer_90d_mes,
    vm.a_vencer_90d_plus as a_vencer_90d_plus_mes,
    
    -- Valores por trimestre
    vt.total_pagar as total_pagar_trimestre,
    vt.quantidade_pagar as quantidade_pagar_trimestre,
    vt.vencido as vencido_trimestre,
    vt.a_vencer_30d as a_vencer_30d_trimestre,
    vt.a_vencer_60d as a_vencer_60d_trimestre,
    vt.a_vencer_90d as a_vencer_90d_trimestre,
    vt.a_vencer_90d_plus as a_vencer_90d_plus_trimestre,
    
    -- Valores por ano
    va.total_pagar as total_pagar_ano,
    va.quantidade_pagar as quantidade_pagar_ano,
    va.vencido as vencido_ano,
    va.a_vencer_30d as a_vencer_30d_ano,
    va.a_vencer_60d as a_vencer_60d_ano,
    va.a_vencer_90d as a_vencer_90d_ano,
    va.a_vencer_90d_plus as a_vencer_90d_plus_ano
    
FROM dados_pagar dp
LEFT JOIN valores_mensais vm ON dp.mes_ano = vm.mes_ano
LEFT JOIN valores_trimestrais vt ON dp.trimestre = vt.trimestre
LEFT JOIN valores_anuais va ON dp.ano = va.ano
ORDER BY dp.vencimento, ABS(dp.valor_original) DESC;

-- ============================================================================
-- VIEW RESUMO RECEBER/PAGAR POR PERÍODO
-- ============================================================================

CREATE OR REPLACE VIEW v_resumo_receber_pagar AS
SELECT 
    COALESCE(r.mes_ano, p.mes_ano) as mes_ano,
    COALESCE(r.trimestre, p.trimestre) as trimestre,
    COALESCE(r.ano, p.ano) as ano,
    
    -- Receber
    COALESCE(r.total_receber_mes, 0) as total_receber,
    COALESCE(r.quantidade_receber_mes, 0) as quantidade_receber,
    COALESCE(r.vencido_mes, 0) as receber_vencido,
    COALESCE(r.a_vencer_30d_mes, 0) as receber_a_vencer_30d,
    
    -- Pagar
    COALESCE(p.total_pagar_mes, 0) as total_pagar,
    COALESCE(p.quantidade_pagar_mes, 0) as quantidade_pagar,
    COALESCE(p.vencido_mes, 0) as pagar_vencido,
    COALESCE(p.a_vencer_30d_mes, 0) as pagar_a_vencer_30d,
    
    -- Saldo
    COALESCE(r.total_receber_mes, 0) - COALESCE(p.total_pagar_mes, 0) as saldo_liquido
    
FROM (
    SELECT DISTINCT mes_ano, trimestre, ano, 
           total_receber_mes, quantidade_receber_mes, vencido_mes, a_vencer_30d_mes
    FROM v_contas_receber
) r
FULL OUTER JOIN (
    SELECT DISTINCT mes_ano, trimestre, ano, 
           total_pagar_mes, quantidade_pagar_mes, vencido_mes, a_vencer_30d_mes
    FROM v_contas_pagar
) p ON r.mes_ano = p.mes_ano
ORDER BY ano, mes_ano;
