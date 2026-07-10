-- Migration: Add 'desenvolvedor' role constraint update
-- Drops the old check_role constraint and adds the updated one including 'desenvolvedor'

ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;

ALTER TABLE users
ADD CONSTRAINT check_role
CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador', 'desenvolvedor'));
