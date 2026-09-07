-- docker/init-scripts/02-create-roles.sql

-- Create a read-only user for the analyzer.
-- This is a SAFETY measure: our tool should NEVER write to
-- the source database. By using a read-only user, we ensure
-- that even if our code has a bug, it can't modify data.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analyzer') THEN
        CREATE USER analyzer WITH PASSWORD 'analyzer_password';
        GRANT CONNECT ON DATABASE postgres TO analyzer;
        GRANT USAGE ON SCHEMA public TO analyzer;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyzer;
    END IF;
END $$;