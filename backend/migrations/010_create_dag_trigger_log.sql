-- Sprint 4 HU-23 — Auditoria de gatilhos manuais das DAGs vetoriais.
--
-- Cada disparo de DAG via POST /airflow/trigger/{dag_id} grava uma linha aqui.
-- O username é desnormalizado pra manter o log legível mesmo se o usuário
-- for deletado. O dag_run_id é o identificador retornado pelo Airflow REST API.

CREATE TABLE IF NOT EXISTS dag_trigger_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(50) NOT NULL,
    user_role VARCHAR(20) NOT NULL,
    dag_id VARCHAR(100) NOT NULL,
    dag_run_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'triggered'
        CHECK (status IN ('triggered', 'failed_to_trigger')),
    error_message TEXT,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dag_trigger_log_dag_id ON dag_trigger_log (dag_id);
CREATE INDEX IF NOT EXISTS idx_dag_trigger_log_triggered_at ON dag_trigger_log (triggered_at DESC);
