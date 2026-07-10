CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operador',
    CONSTRAINT check_role CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador'))
);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'operador';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_role'
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT check_role
        CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador'));
    END IF;
END $$;
