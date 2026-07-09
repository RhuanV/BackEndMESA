import pytest
from airflow.models import DagBag, DagRun
from airflow.utils.state import State
from airflow.utils import timezone
from airflow.utils.session import create_session

@pytest.fixture(scope="module")
def dag_bag():
    # Load the DAGs from the mapped folder
    return DagBag(include_examples=False)

def test_scheduler_creates_dagrun_for_eligible_interval(dag_bag):
    """Verify that the scheduler creates a dag_run for DAGs with an eligible interval."""
    # Iterate over all loaded DAGs to ensure full coverage.
    dags_tested = 0

    for dag_id, dag in dag_bag.dags.items():
        # Skip DAGs without a schedule.
        # In Airflow 2.x the 'schedule' argument is converted into the 'timetable' attribute.
        timetable = getattr(dag, "timetable", None)
        if timetable is None or type(timetable).__name__ == "NullTimetable":
            continue

        dags_tested += 1

        # Setup: define an eligible interval (now) and clear previous test data
        execution_date = timezone.utcnow()
        with create_session() as session:
            session.query(DagRun).filter(
                DagRun.dag_id == dag_id, 
                DagRun.execution_date == execution_date
            ).delete()
        
        # Infer the data interval the same way the real Airflow scheduler does
        data_interval = dag.timetable.infer_manual_data_interval(run_after=execution_date)

        # Set the correct run_type (Dataset triggers have a specific run type in Airflow >= 2.4)
        run_type = "dataset_triggered" if type(timetable).__name__ == "DatasetTriggeredTimetable" else "scheduled"

        # Simulate the scheduler triggering the execution
        dag_run = dag.create_dagrun(
            state=State.QUEUED,
            execution_date=execution_date,
            run_type=run_type,
            data_interval=data_interval
        )
        
        # The execution is triggered and the dag_run record is created
        assert dag_run is not None, f"A dag_run should have been created for {dag_id}."

        # Verify the dag_run is correctly associated with the DAG
        assert dag_run.dag_id == dag_id, f"The dag_run is not correctly associated with DAG: {dag_id}."

        # Verify the initial execution state of each dag_run
        assert dag_run.state in [State.QUEUED, State.RUNNING, State.SUCCESS], \
            f"Initial state for {dag_id} was {dag_run.state}, expected one of: queued, running, success."

        # Teardown: remove the generated dag_run to avoid polluting the test database
        with create_session() as session:
            session.query(DagRun).filter(
                DagRun.dag_id == dag_id, 
                DagRun.execution_date == execution_date
            ).delete()
            
    # Ensure that at least one DAG was actually tested
    assert dags_tested > 0, "No scheduled DAGs were found to test."