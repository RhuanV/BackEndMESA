import os
import re
import pytest
from airflow.models import DagModel, DagRun
from airflow.utils.session import create_session

INIT_SCRIPT_PATH = "/opt/airflow/init_airflow.sh"

@pytest.fixture(scope="module")
def init_commands():
    """
    Test Strategy: Validation of commands executed in the airflow-init service.
    Reads the Airflow initialization script to dynamically extract 
    which DAGs were configured for automatic unpause and trigger.
    """
    assert os.path.exists(INIT_SCRIPT_PATH), \
        f"Script {INIT_SCRIPT_PATH} not found. Check the mapping in docker-compose.yml."

    unpaused_dags = set()
    triggered_dags = set()

    with open(INIT_SCRIPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        # Extracts DAGs from the 'airflow dags unpause [dag_id]' command, ignoring flags like '-e'
        unpause_matches = re.findall(r"airflow\s+dags\s+unpause\s+(?:-[^\s]+\s+)*([a-zA-Z0-9_-]+)", content)
        unpaused_dags.update(unpause_matches)

        # Extracts DAGs from the 'airflow dags trigger [dag_id]' command
        trigger_matches = re.findall(r"airflow\s+dags\s+trigger\s+(?:-[^\s]+\s+)*([a-zA-Z0-9_-]+)", content)
        triggered_dags.update(trigger_matches)

    return {
        "unpaused": list(unpaused_dags),
        "triggered": list(triggered_dags)
    }

def test_initialization_dags_are_active_and_triggered(init_commands):
    """
    Acceptance Criteria: DAGs are unpaused and executions are triggered automatically.
    Test Strategy: Verification of registered executions.
    """
    with create_session() as session:
        for dag_id in init_commands["unpaused"]:
            dag_model = session.query(DagModel).filter(DagModel.dag_id == dag_id).first()
            
            assert dag_model is not None, f"DAG '{dag_id}' defined in init_script does not exist in the database."
            assert dag_model.is_paused is False, f"DAG '{dag_id}' should be unpaused."

        for dag_id in init_commands["triggered"]:
            runs = session.query(DagRun).filter(DagRun.dag_id == dag_id).all()
            
            assert len(runs) > 0, f"DAG '{dag_id}' should have at least one automatically registered execution (DagRun)."