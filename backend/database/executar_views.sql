-- ============================================================================
-- SCRIPT PARA EXECUTAR TODAS AS VIEWS
-- ============================================================================

-- Executar este script no PostgreSQL para criar todas as views

-- 1. Views DRE
\i views_dre.sql

-- 2. Views DFC  
\i views_dfc.sql

-- 3. Views Receber/Pagar
\i views_receber_pagar.sql

-- ============================================================================
-- VERIFICAÇÃO DAS VIEWS CRIADAS
-- ============================================================================

-- Listar todas as views criadas
SELECT 
    schemaname,
    viewname,
    definition
FROM pg_views 
WHERE schemaname = 'public' 
AND viewname LIKE 'v_%'
ORDER BY viewname;

-- ============================================================================
-- TESTES DAS VIEWS
-- ============================================================================

-- Teste DRE
SELECT 'DRE Completo' as view, COUNT(*) as registros FROM v_dre_completo
UNION ALL
SELECT 'DRE Resumida' as view, COUNT(*) as registros FROM v_dre_resumida
UNION ALL
SELECT 'DRE Por Período' as view, COUNT(*) as registros FROM v_dre_por_periodo;

-- Teste DFC
SELECT 'DFC Completo' as view, COUNT(*) as registros FROM v_dfc_completo
UNION ALL
SELECT 'DFC Resumida' as view, COUNT(*) as registros FROM v_dfc_resumida
UNION ALL
SELECT 'DFC Por Período' as view, COUNT(*) as registros FROM v_dfc_por_periodo
UNION ALL
SELECT 'DFC Saldo Acumulado' as view, COUNT(*) as registros FROM v_dfc_saldo_acumulado;

-- Teste Receber/Pagar
SELECT 'Contas Receber' as view, COUNT(*) as registros FROM v_contas_receber
UNION ALL
SELECT 'Contas Pagar' as view, COUNT(*) as registros FROM v_contas_pagar
UNION ALL
SELECT 'Resumo Receber/Pagar' as view, COUNT(*) as registros FROM v_resumo_receber_pagar;

-- ============================================================================
-- EXEMPLOS DE CONSULTAS ÚTEIS
-- ============================================================================

-- DRE: Top 5 categorias por resultado
SELECT 
    dre_n2,
    SUM(resultado_mes) as resultado_total,
    COUNT(*) as registros
FROM v_dre_completo
GROUP BY dre_n2
ORDER BY resultado_total DESC
LIMIT 5;

-- DFC: Fluxo de caixa por mês
SELECT 
    mes_ano,
    SUM(fluxo_liquido_mes) as fluxo_liquido_mes,
    SUM(fluxo_liquido_orc_mes) as fluxo_liquido_orc_mes
FROM v_dfc_completo
GROUP BY mes_ano
ORDER BY mes_ano;

-- Receber: Contas vencidas
SELECT 
    dre_n2,
    SUM(valor_original) as total_vencido,
    COUNT(*) as quantidade_vencida
FROM v_contas_receber
WHERE status_vencimento = 'vencido'
GROUP BY dre_n2
ORDER BY total_vencido DESC;

-- Pagar: Contas a vencer em 30 dias
SELECT 
    dre_n2,
    SUM(ABS(valor_original)) as total_a_vencer_30d,
    COUNT(*) as quantidade_a_vencer_30d
FROM v_contas_pagar
WHERE status_vencimento = 'a_vencer_30d'
GROUP BY dre_n2
ORDER BY total_a_vencer_30d DESC;
