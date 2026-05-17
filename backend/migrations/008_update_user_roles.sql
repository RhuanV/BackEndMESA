-- Sprint 3 — Atualiza o conjunto de perfis de usuário para os 5 perfis MESA-A
-- definidos pela PO: coordenador, gestor, supervisor, operador, administrador.
--
-- Mapeamento dos perfis antigos:
--   analyst -> operador        (tratamento de dados e vetorização)
--   admin   -> coordenador     (permissão total, gerencia acesso, aprova entregáveis)
--   dev     -> administrador   (config do sistema, logs, pipelines)
--
-- Idempotente: pode rodar mais de uma vez sem erro (CHECK é dropado/recriado,
-- UPDATE só toca em linhas com valor antigo).

ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;

UPDATE users SET role = 'operador'      WHERE role = 'analyst';
UPDATE users SET role = 'coordenador'   WHERE role = 'admin';
UPDATE users SET role = 'administrador' WHERE role = 'dev';

ALTER TABLE users ALTER COLUMN role SET DEFAULT 'operador';

ALTER TABLE users
ADD CONSTRAINT check_role
CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador'));
