"""Verify DAG integrity: loading without errors and absence of cycles."""
import pytest
from airflow.models import DagBag
from airflow.utils.dag_cycle_tester import check_cycle

@pytest.fixture(scope="session")
def dag_bag():
    # Load and compile the DAGs once, reusing them across tests.
    return DagBag(include_examples=False)

def test_dags_load_with_no_errors(dag_bag):
    """Verify that there are no import errors when loading the DAGs."""
    assert len(dag_bag.import_errors) == 0, \
        f"Failed to load the following DAGs: {dag_bag.import_errors}"

def test_dags_have_no_cycles(dag_bag):
    """Verify that no DAG has circular dependencies."""
    for dag_id, dag in dag_bag.dags.items():
        check_cycle(dag)  # Airflow raises AirflowDagCycleException if there is a cycle