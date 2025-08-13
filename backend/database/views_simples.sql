-- ============================================================================
-- VIEWS SQL SIMPLES PARA TESTE
-- ============================================================================

-- View DRE básica
CREATE OR REPLACE VIEW v_dre_simples AS
SELECT 
    dre_n2,
    dre_n1,
    classificacao,
    valor_original,
    origem,
    competencia,
    empresa,
    COUNT(*) as total_registros,
    SUM(CASE WHEN valor_original > 0 THEN valor_original ELSE 0 END) as receitas,
    SUM(CASE WHEN valor_original < 0 THEN ABS(valor_original) ELSE 0 END) as despesas,
    SUM(valor_original) as resultado_liquido
FROM financial_data 
WHERE dre_n2 IS NOT NULL 
AND dre_n2 != '' 
AND dre_n2 != 'nan'
AND valor_original IS NOT NULL
AND competencia IS NOT NULL
GROUP BY dre_n2, dre_n1, classificacao, valor_original, origem, competencia, empresa;

-- View DFC básica
CREATE OR REPLACE VIEW v_dfc_simples AS
SELECT 
    dfc_n2,
    dfc_n1,
    classificacao,
    valor_original,
    origem,
    competencia,
    empresa,
    COUNT(*) as total_registros,
    SUM(CASE WHEN valor_original > 0 THEN valor_original ELSE 0 END) as entradas,
    SUM(CASE WHEN valor_original < 0 THEN ABS(valor_original) ELSE 0 END) as saidas,
    SUM(valor_original) as fluxo_liquido
FROM financial_data 
WHERE dfc_n2 IS NOT NULL 
AND dfc_n2 != '' 
AND dfc_n2 != 'nan'
AND valor_original IS NOT NULL
AND competencia IS NOT NULL
GROUP BY dfc_n2, dfc_n1, classificacao, valor_original, origem, competencia, empresa;

-- View Receber básica
CREATE OR REPLACE VIEW v_receber_simples AS
SELECT 
    dre_n2,
    classificacao,
    valor_original,
    competencia,
    vencimento,
    empresa,
    COUNT(*) as total_registros,
    SUM(valor_original) as total_receber
FROM financial_data 
WHERE valor_original > 0
AND vencimento IS NOT NULL
AND competencia IS NOT NULL
GROUP BY dre_n2, classificacao, valor_original, competencia, vencimento, empresa;

-- View Pagar básica
CREATE OR REPLACE VIEW v_pagar_simples AS
SELECT 
    dre_n2,
    classificacao,
    valor_original,
    competencia,
    vencimento,
    empresa,
    COUNT(*) as total_registros,
    SUM(ABS(valor_original)) as total_pagar
FROM financial_data 
WHERE valor_original < 0
AND vencimento IS NOT NULL
AND competencia IS NOT NULL
GROUP BY dre_n2, classificacao, valor_original, competencia, vencimento, empresa;
