-- ============================================================================
-- VIEWS PARA DRE NÍVEL 0 (Estrutura principal da aba 'dre')
-- ============================================================================

-- View principal DRE N0 com dados agregados
CREATE OR REPLACE VIEW v_dre_n0_completo AS
WITH dados_agregados AS (
    SELECT 
        -- Estrutura DRE N0
        ds0.id as dre_n0_id,
        ds0.name as nome_conta,
        ds0.operation_type as tipo_operacao,
        ds0.order_index as ordem,
        ds0.description as descricao,
        
        -- Dados financeiros agregados
        fd.origem,
        fd.empresa,
        fd.competencia,
        fd.valor_original,
        
        -- Períodos para agregação
        EXTRACT(YEAR FROM fd.competencia) as ano,
        EXTRACT(MONTH FROM fd.competencia) as mes,
        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
        TO_CHAR(fd.competencia, 'YYYY-Q') || EXTRACT(QUARTER FROM fd.competencia) as periodo_trimestral,
        EXTRACT(YEAR FROM fd.competencia) as periodo_anual
        
    FROM dre_structure_n0 ds0
    LEFT JOIN financial_data fd ON (
        -- Relacionar com dados financeiros baseado na estrutura DRE
        fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL
    )
    WHERE ds0.is_active = true
),
agregacoes AS (
    SELECT 
        dre_n0_id,
        nome_conta,
        tipo_operacao,
        ordem,
        descricao,
        origem,
        empresa,
        ano,
        mes,
        periodo_mensal,
        periodo_trimestral,
        periodo_anual,
        
        -- Valores agregados por período
        SUM(CASE WHEN valor_original IS NOT NULL THEN valor_original ELSE 0 END) as valor_periodo,
        COUNT(*) as quantidade_registros
        
    FROM dados_agregados
    GROUP BY 
        dre_n0_id, nome_conta, tipo_operacao, ordem, descricao, 
        origem, empresa, ano, mes, periodo_mensal, periodo_trimestral, periodo_anual
),
valores_finais AS (
    SELECT 
        dre_n0_id,
        nome_conta,
        tipo_operacao,
        ordem,
        descricao,
        origem,
        empresa,
        
        -- Valores mensais
        SUM(CASE WHEN periodo_mensal = '2025-01' THEN valor_periodo ELSE 0 END) as valor_2025_01,
        SUM(CASE WHEN periodo_mensal = '2025-02' THEN valor_periodo ELSE 0 END) as valor_2025_02,
        SUM(CASE WHEN periodo_mensal = '2025-03' THEN valor_periodo ELSE 0 END) as valor_2025_03,
        SUM(CASE WHEN periodo_mensal = '2025-04' THEN valor_periodo ELSE 0 END) as valor_2025_04,
        SUM(CASE WHEN periodo_mensal = '2025-05' THEN valor_periodo ELSE 0 END) as valor_2025_05,
        SUM(CASE WHEN periodo_mensal = '2025-06' THEN valor_periodo ELSE 0 END) as valor_2025_06,
        SUM(CASE WHEN periodo_mensal = '2025-07' THEN valor_periodo ELSE 0 END) as valor_2025_07,
        SUM(CASE WHEN periodo_mensal = '2025-08' THEN valor_periodo ELSE 0 END) as valor_2025_08,
        SUM(CASE WHEN periodo_mensal = '2025-09' THEN valor_periodo ELSE 0 END) as valor_2025_09,
        SUM(CASE WHEN periodo_mensal = '2025-10' THEN valor_periodo ELSE 0 END) as valor_2025_10,
        SUM(CASE WHEN periodo_mensal = '2025-11' THEN valor_periodo ELSE 0 END) as valor_2025_11,
        SUM(CASE WHEN periodo_mensal = '2025-12' THEN valor_periodo ELSE 0 END) as valor_2025_12,
        
        -- Valores trimestrais
        SUM(CASE WHEN periodo_trimestral = '2025-Q1' THEN valor_periodo ELSE 0 END) as valor_2025_q1,
        SUM(CASE WHEN periodo_trimestral = '2025-Q2' THEN valor_periodo ELSE 0 END) as valor_2025_q2,
        SUM(CASE WHEN periodo_trimestral = '2025-Q3' THEN valor_periodo ELSE 0 END) as valor_2025_q3,
        SUM(CASE WHEN periodo_trimestral = '2025-Q4' THEN valor_periodo ELSE 0 END) as valor_2025_q4,
        
        -- Valores anuais
        SUM(CASE WHEN periodo_anual = 2025 THEN valor_periodo ELSE 0 END) as valor_2025,
        SUM(CASE WHEN periodo_anual = 2024 THEN valor_periodo ELSE 0 END) as valor_2024,
        
        -- Total geral
        SUM(valor_periodo) as valor_total
        
    FROM agregacoes
    GROUP BY dre_n0_id, nome_conta, tipo_operacao, ordem, descricao, origem, empresa
)
SELECT 
    dre_n0_id,
    nome_conta,
    tipo_operacao,
    ordem,
    descricao,
    origem,
    empresa,
    
    -- Valores mensais como JSON
    json_build_object(
        '2025-01', valor_2025_01,
        '2025-02', valor_2025_02,
        '2025-03', valor_2025_03,
        '2025-04', valor_2025_04,
        '2025-05', valor_2025_05,
        '2025-06', valor_2025_06,
        '2025-07', valor_2025_07,
        '2025-08', valor_2025_08,
        '2025-09', valor_2025_09,
        '2025-10', valor_2025_10,
        '2025-11', valor_2025_11,
        '2025-12', valor_2025_12
    ) as valores_mensais,
    
    -- Valores trimestrais como JSON
    json_build_object(
        '2025-Q1', valor_2025_q1,
        '2025-Q2', valor_2025_q2,
        '2025-Q3', valor_2025_q3,
        '2025-Q4', valor_2025_q4
    ) as valores_trimestrais,
    
    -- Valores anuais como JSON
    json_build_object(
        '2025', valor_2025,
        '2024', valor_2024
    ) as valores_anuais,
    
    -- Orçamentos (zerados por enquanto, podem ser adicionados depois)
    json_build_object() as orcamentos_mensais,
    json_build_object() as orcamentos_trimestrais,
    json_build_object() as orcamentos_anuais,
    0 as orcamento_total,
    
    valor_total,
    origem as source
    
FROM valores_finais
ORDER BY ordem;

-- View simplificada para DRE N0
CREATE OR REPLACE VIEW v_dre_n0_simples AS
SELECT 
    dre_n0_id,
    nome_conta,
    tipo_operacao,
    ordem,
    descricao,
    origem,
    empresa,
    valor_total,
    source
FROM v_dre_n0_completo;

-- View para DRE N0 por período específico
CREATE OR REPLACE VIEW v_dre_n0_por_periodo AS
SELECT 
    dre_n0_id,
    nome_conta,
    tipo_operacao,
    ordem,
    descricao,
    origem,
    empresa,
    periodo_mensal,
    periodo_trimestral,
    periodo_anual,
    valor_periodo
FROM (
    SELECT 
        ds0.id as dre_n0_id,
        ds0.name as nome_conta,
        ds0.operation_type as tipo_operacao,
        ds0.order_index as ordem,
        ds0.description as descricao,
        fd.origem,
        fd.empresa,
        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
        TO_CHAR(fd.competencia, 'YYYY-Q') || EXTRACT(QUARTER FROM fd.competencia) as periodo_trimestral,
        EXTRACT(YEAR FROM fd.competencia) as periodo_anual,
        SUM(fd.valor_original) as valor_periodo
    FROM dre_structure_n0 ds0
    LEFT JOIN financial_data fd ON (
        fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL
    )
    WHERE ds0.is_active = true
    GROUP BY 
        ds0.id, ds0.name, ds0.operation_type, ds0.order_index, ds0.description,
        fd.origem, fd.empresa, fd.competencia
) dados
ORDER BY ordem, periodo_mensal;

-- Comentários das views
COMMENT ON VIEW v_dre_n0_completo IS 'View completa para DRE Nível 0 com todos os dados agregados';
COMMENT ON VIEW v_dre_n0_simples IS 'View simplificada para DRE Nível 0';
COMMENT ON VIEW v_dre_n0_por_periodo IS 'View para DRE Nível 0 com dados por período';
