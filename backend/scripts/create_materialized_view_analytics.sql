-- Script para criar view materializada com análises pré-calculadas
-- Esta view materializada pré-calcula análises horizontal e vertical para melhorar performance

-- 1. Criar view materializada para análises
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dre_n0_analytics AS
WITH dados_agregados AS (
    SELECT 
        fd.dre_n2,
        fd.dre_n1,
        fd.competencia,
        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
        SUM(fd.valor_original) as valor_total
    FROM financial_data fd
    WHERE fd.dre_n2 IS NOT NULL 
    AND fd.valor_original IS NOT NULL 
    AND fd.competencia IS NOT NULL
    GROUP BY fd.dre_n2, fd.dre_n1, fd.competencia
),
analises_horizontais AS (
    SELECT 
        dre_n2,
        dre_n1,
        periodo_mensal,
        periodo_trimestral,
        periodo_anual,
        valor_total,
        LAG(valor_total) OVER (
            PARTITION BY dre_n2, dre_n1 
            ORDER BY competencia
        ) as valor_anterior_mensal,
        LAG(valor_total) OVER (
            PARTITION BY dre_n2, dre_n1 
            ORDER BY periodo_trimestral
        ) as valor_anterior_trimestral,
        LAG(valor_total) OVER (
            PARTITION BY dre_n2, dre_n1 
            ORDER BY periodo_anual
        ) as valor_anterior_anual
    FROM dados_agregados
),
analises_verticais AS (
    SELECT 
        dre_n2,
        dre_n1,
        periodo_mensal,
        periodo_trimestral,
        periodo_anual,
        valor_total,
        SUM(valor_total) OVER (PARTITION BY periodo_mensal) as total_mensal,
        SUM(valor_total) OVER (PARTITION BY periodo_trimestral) as total_trimestral,
        SUM(valor_total) OVER (PARTITION BY periodo_anual) as total_anual
    FROM dados_agregados
)
SELECT 
    ah.dre_n2,
    ah.dre_n1,
    ah.periodo_mensal,
    ah.periodo_trimestral,
    ah.periodo_anual,
    ah.valor_total,
    -- Análise Horizontal Mensal
    CASE 
        WHEN ah.valor_anterior_mensal IS NULL OR ah.valor_anterior_mensal = 0 THEN '–'
        ELSE ROUND(((ah.valor_total - ah.valor_anterior_mensal) / ah.valor_anterior_mensal * 100), 2)::text || '%'
    END as analise_horizontal_mensal,
    -- Análise Horizontal Trimestral
    CASE 
        WHEN ah.valor_anterior_trimestral IS NULL OR ah.valor_anterior_trimestral = 0 THEN '–'
        ELSE ROUND(((ah.valor_total - ah.valor_anterior_trimestral) / ah.valor_anterior_trimestral * 100), 2)::text || '%'
    END as analise_horizontal_trimestral,
    -- Análise Horizontal Anual
    CASE 
        WHEN ah.valor_anterior_anual IS NULL OR ah.valor_anterior_anual = 0 THEN '–'
        ELSE ROUND(((ah.valor_total - ah.valor_anterior_anual) / ah.valor_anterior_anual * 100), 2)::text || '%'
    END as analise_horizontal_anual,
    -- Análise Vertical Mensal
    CASE 
        WHEN av.total_mensal = 0 THEN '–'
        ELSE ROUND((ah.valor_total / av.total_mensal * 100), 2)::text || '%'
    END as analise_vertical_mensal,
    -- Análise Vertical Trimestral
    CASE 
        WHEN av.total_trimestral = 0 THEN '–'
        ELSE ROUND((ah.valor_total / av.total_trimestral * 100), 2)::text || '%'
    END as analise_vertical_trimestral,
    -- Análise Vertical Anual
    CASE 
        WHEN av.total_anual = 0 THEN '–'
        ELSE ROUND((ah.valor_total / av.total_anual * 100), 2)::text || '%'
    END as analise_vertical_anual,
    -- Timestamp de criação
    NOW() as ultima_atualizacao
FROM analises_horizontais ah
JOIN analises_verticais av ON (
    ah.dre_n2 = av.dre_n2 
    AND ah.dre_n1 = av.dre_n1 
    AND ah.periodo_mensal = av.periodo_mensal
    AND ah.periodo_trimestral = av.periodo_trimestral
    AND ah.periodo_anual = av.periodo_anual
);

-- 2. Criar índices na view materializada para otimizar consultas
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_dre2 
ON mv_dre_n0_analytics (dre_n2);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_periodo 
ON mv_dre_n0_analytics (periodo_mensal, periodo_trimestral, periodo_anual);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_dre_analytics_completo 
ON mv_dre_n0_analytics (dre_n2, periodo_mensal, periodo_trimestral, periodo_anual);

-- 3. Criar função para atualizar a view materializada
CREATE OR REPLACE FUNCTION refresh_dre_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dre_n0_analytics;
    RAISE NOTICE 'View materializada mv_dre_n0_analytics atualizada em %', NOW();
END;
$$ LANGUAGE plpgsql;

-- 4. Criar função para buscar análises da view materializada
CREATE OR REPLACE FUNCTION get_dre_analytics(
    p_dre_n2 text,
    p_periodo_mensal text DEFAULT NULL,
    p_periodo_trimestral text DEFAULT NULL,
    p_periodo_anual text DEFAULT NULL
)
RETURNS TABLE (
    dre_n2 text,
    dre_n1 text,
    periodo_mensal text,
    periodo_trimestral text,
    periodo_anual text,
    valor_total numeric,
    analise_horizontal_mensal text,
    analise_horizontal_trimestral text,
    analise_horizontal_anual text,
    analise_vertical_mensal text,
    analise_vertical_trimestral text,
    analise_vertical_anual text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mv.dre_n2,
        mv.dre_n1,
        mv.periodo_mensal,
        mv.periodo_trimestral,
        mv.periodo_anual,
        mv.valor_total,
        mv.analise_horizontal_mensal,
        mv.analise_horizontal_trimestral,
        mv.analise_horizontal_anual,
        mv.analise_vertical_mensal,
        mv.analise_vertical_trimestral,
        mv.analise_vertical_anual
    FROM mv_dre_n0_analytics mv
    WHERE mv.dre_n2 = p_dre_n2
    AND (p_periodo_mensal IS NULL OR mv.periodo_mensal = p_periodo_mensal)
    AND (p_periodo_trimestral IS NULL OR mv.periodo_trimestral = p_periodo_trimestral)
    AND (p_periodo_anual IS NULL OR mv.periodo_anual = p_periodo_anual)
    ORDER BY mv.periodo_mensal, mv.periodo_trimestral, mv.periodo_anual;
END;
$$ LANGUAGE plpgsql;

-- 5. Verificar estatísticas
ANALYZE mv_dre_n0_analytics;

-- 6. Mostrar informações da view materializada
SELECT 
    schemaname,
    matviewname,
    matviewowner,
    definition
FROM pg_matviews 
WHERE matviewname = 'mv_dre_n0_analytics';

-- 7. Mostrar estatísticas de uso
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'mv_dre_n0_analytics'
ORDER BY indexname;
