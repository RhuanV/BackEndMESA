"""
Test Suite: DAG Integrity

User Story: As a developer, I want to ensure that all DAGs are loaded without errors, 
to avoid failures at runtime.

Test Strategy: Unit test using DagBag, verifying the absence of import errors.
"""
import pytest
from airflow.models import DagBag
from airflow.utils.dag_cycle_tester import check_cycle

@pytest.fixture(scope="session")
def dag_bag():
    # DagBag reads the Python files and compiles the DAGs.
    # We use a fixture to load this only once and reuse it across tests.
    return DagBag(include_examples=False)

def test_dags_load_with_no_errors(dag_bag):
    """
    Acceptance Criteria:
    - Given a set of files in the DAGs folder
    - When Airflow is started
    - Then: There are no DAG import errors, and all DAGs are registered in the system.
    """
    # If there are errors (e.g., missing package, typo), they are saved in 'import_errors'
    assert len(dag_bag.import_errors) == 0, \
        f"Failed to load the following DAGs: {dag_bag.import_errors}"

def test_dags_have_no_cycles(dag_bag):
    """
    Tests that no DAG has circular dependencies (e.g., Task A -> Task B -> Task A).
    Circular dependencies prevent DAGs from executing properly.
    """
    for dag_id, dag in dag_bag.dags.items():
        check_cycle(dag)  # Airflow will raise an AirflowDagCycleException if there is a cycle