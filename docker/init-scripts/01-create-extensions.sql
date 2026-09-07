-- docker/init-scripts/01-create-extensions.sql

-- Enable HypoPG: Allows us to test "hypothetical" indexes
-- without actually building them. This is how we check for
-- regressions (whether a new index would slow down other queries)
CREATE EXTENSION IF NOT EXISTS hypopg;

-- Enable pg_stat_statements: Tracks query execution statistics
-- This tells us which queries are slow and how often they run
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Confirm everything worked (we'll see this in the logs)
DO $$
BEGIN
    RAISE NOTICE 'HypoPG installed: %', 
        (SELECT COUNT(*) FROM pg_extension WHERE extname = 'hypopg');
    RAISE NOTICE 'pg_stat_statements installed: %', 
        (SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements');
END $$;