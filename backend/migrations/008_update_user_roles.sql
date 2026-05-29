-- Sprint 3 — Updates the set of user roles to the 5 MESA-A roles
-- defined by the PO: coordinator, manager, supervisor, operator, administrator.
--
-- Mapping of old roles:
--   analyst -> operador        (data processing and vectorization)
--   admin   -> coordenador     (full permission, manages access, approves deliverables)
--   dev     -> administrador   (system config, logs, pipelines)
--
-- Idempotent: can run more than once without error (CHECK is dropped/recreated,
-- UPDATE only touches rows with old values).

ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;

UPDATE users SET role = 'operador'      WHERE role = 'analyst';
UPDATE users SET role = 'coordenador'   WHERE role = 'admin';
UPDATE users SET role = 'administrador' WHERE role = 'dev';

ALTER TABLE users ALTER COLUMN role SET DEFAULT 'operador';

ALTER TABLE users
ADD CONSTRAINT check_role
CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador'));
