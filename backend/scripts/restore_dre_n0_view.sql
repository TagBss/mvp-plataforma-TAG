-- ============================================================================
-- SCRIPT PARA RESTAURAR A VIEW DRE N0
-- ============================================================================
-- Execute este script no PostgreSQL quando o banco estiver rodando

-- Remover view existente
DROP VIEW IF EXISTS v_dre_n0_completo CASCADE;

-- Criar view restaurada
CREATE OR REPLACE VIEW v_dre_n0_completo AS
WITH valores_agregados AS (
    SELECT 
        ds0.id as dre_n0_id,
        ds0.name as nome_conta,
        ds0.operation_type as tipo_operacao,
        ds0.order_index as ordem,
        ds0.description as descricao,
        ds0.empresa_id,
        
        -- Períodos
        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
        TO_CHAR(fd.competencia, 'YYYY-Q') || EXTRACT(QUARTER FROM fd.competencia) as periodo_trimestral,
        EXTRACT(YEAR FROM fd.competencia) as periodo_anual,
        
        -- Valores
        SUM(fd.valor_original) as valor_periodo
        
    FROM dre_structure_n0 ds0
    LEFT JOIN financial_data fd ON (
        fd.dre_n1_id = ds0.id OR fd.dre_n2_id = ds0.id
    )
    WHERE ds0.is_active = true
    GROUP BY 
        ds0.id, ds0.name, ds0.operation_type, ds0.order_index, ds0.description, ds0.empresa_id,
        fd.competencia
),
valores_finais AS (
    SELECT 
        dre_n0_id,
        nome_conta,
        tipo_operacao,
        ordem,
        descricao,
        empresa_id,
        
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
        
    FROM valores_agregados
    GROUP BY dre_n0_id, nome_conta, tipo_operacao, ordem, descricao, empresa_id
)
SELECT 
    dre_n0_id,
    nome_conta,
    tipo_operacao,
    ordem,
    descricao,
    empresa_id,
    
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
    
    -- Orçamentos (zerados por enquanto)
    json_build_object() as orcamentos_mensais,
    json_build_object() as orcamentos_trimestrais,
    json_build_object() as orcamentos_anuais,
    0 as orcamento_total,
    
    valor_total,
    'postgresql' as source
    
FROM valores_finais
ORDER BY ordem;

-- Comentário da view
COMMENT ON VIEW v_dre_n0_completo IS 'View restaurada para DRE Nível 0 com dados agregados';

-- Verificar se a view foi criada
SELECT 'View v_dre_n0_completo criada com sucesso!' as status;

-- Testar a view
SELECT COUNT(*) as total_registros FROM v_dre_n0_completo;
