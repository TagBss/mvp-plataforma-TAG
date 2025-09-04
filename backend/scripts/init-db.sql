-- 🗄️ Script de Inicialização do Banco PostgreSQL
-- Executado automaticamente quando o container PostgreSQL é criado

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Criar usuário adicional se necessário (opcional)
-- CREATE USER app_user WITH PASSWORD 'app_password';
-- GRANT ALL PRIVILEGES ON DATABASE tag_financeiro TO app_user;

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
-- ALTER SYSTEM SET pg_stat_statements.track = 'all'; -- Comentado pois causa erro no PostgreSQL 15

-- Log de inicialização
DO $$
BEGIN
    RAISE NOTICE '✅ Banco de dados tag_financeiro inicializado com sucesso!';
    RAISE NOTICE '📅 Data/Hora: %', NOW();
    RAISE NOTICE '🌍 Timezone: %', current_setting('timezone');
END $$;

