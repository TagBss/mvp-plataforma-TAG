-- Script para criar índices compostos otimizados para performance do DRE
-- Executar como superusuário ou usuário com permissões CREATE INDEX

-- 1. Índice composto para queries principais do DRE (dre_n2, dre_n1, competencia, valor_original)
-- Otimiza queries que filtram por conta DRE e período
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_dre_comp 
ON financial_data (dre_n2, dre_n1, competencia, valor_original);

-- 2. Índice composto para filtros por período (competencia, dre_n2, valor_original)
-- Otimiza queries que filtram por período específico
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_periodo 
ON financial_data (competencia, dre_n2, valor_original);

-- 3. Índice composto para classificações (dre_n2, classificacao, competencia, valor_original)
-- Otimiza queries de classificações expandidas
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_classificacoes 
ON financial_data (dre_n2, classificacao, competencia, valor_original);

-- 4. Índice para estrutura DRE N0 (is_active, order_index)
-- Otimiza queries da estrutura hierárquica
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dre_structure_n0_active_order 
ON dre_structure_n0 (is_active, order_index);

-- 5. Índice para competência (competencia) - para ordenação cronológica
-- Otimiza ORDER BY competencia
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_competencia 
ON financial_data (competencia);

-- 6. Índice composto para análises (dre_n2, competencia, valor_original)
-- Otimiza cálculos de análise horizontal e vertical
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_analises 
ON financial_data (dre_n2, competencia, valor_original);

-- 7. Índice para valores não nulos (valor_original IS NOT NULL)
-- Otimiza filtros WHERE valor_original IS NOT NULL
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_valor_not_null 
ON financial_data (valor_original) WHERE valor_original IS NOT NULL;

-- 8. Índice para dre_n2 não nulos (dre_n2 IS NOT NULL)
-- Otimiza filtros WHERE dre_n2 IS NOT NULL
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_data_dre2_not_null 
ON financial_data (dre_n2) WHERE dre_n2 IS NOT NULL;

-- Verificar estatísticas dos índices
ANALYZE financial_data;
ANALYZE dre_structure_n0;

-- Mostrar índices criados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('financial_data', 'dre_structure_n0')
ORDER BY tablename, indexname;

-- Mostrar estatísticas de uso dos índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('financial_data', 'dre_structure_n0')
ORDER BY tablename, indexname;
