CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'analista',
    CONSTRAINT check_role CHECK (role IN ('analista', 'administrador', 'desenvolvedor'))
);

ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'analista';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_role'
    ) THEN
        ALTER TABLE usuarios
        ADD CONSTRAINT check_role
        CHECK (role IN ('analista', 'administrador', 'desenvolvedor'));
    END IF;
END $$;