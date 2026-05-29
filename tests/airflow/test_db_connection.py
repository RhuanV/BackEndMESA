import pytest
from airflow.providers.postgres.hooks.postgres import PostgresHook

def test_airflow_main_db_connection():
    """
    User Story: As a system, I want Airflow to be able to connect to the main database, 
    to allow the execution of data pipelines.
    
    Test Strategy: Connection test via BaseHook (implemented via PostgresHook) 
    and execution of basic queries.
    """
    # The connection ID defined in docker-compose.yml via AIRFLOW_CONN_GEOAVIA_MAIN_CONN
    conn_id = "geoavia_main_conn"
    
    # 1. Acceptance Criteria: The configured connection exists in Airflow
    try:
        hook = PostgresHook(postgres_conn_id=conn_id)
    except Exception as e:
        pytest.fail(f"Failed to initialize hook for connection '{conn_id}'. Error: {e}")
        
    # 2. Acceptance Criteria: Allows valid authentication
    try:
        # get_conn() actually opens the connection to the database
        conn = hook.get_conn()
        assert conn is not None, "Connection object should not be None."
    except Exception as e:
        pytest.fail(f"Failed to authenticate using connection '{conn_id}'. Error: {e}")
        
    # 3. Acceptance Criteria: Allows execution of simple queries
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert result is not None and result[0] == 1, "The query 'SELECT 1;' should return 1."
        cursor.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Failed to execute a basic query on connection '{conn_id}'. Error: {e}")