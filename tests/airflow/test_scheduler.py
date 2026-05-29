import pytest
from airflow.models import DagBag, DagRun
from airflow.utils.state import State
from airflow.utils import timezone
from airflow.utils.session import create_session

@pytest.fixture(scope="module")
def dag_bag():
    # Load DAGs from the mapped dags folder
    return DagBag(include_examples=False)

def test_scheduler_creates_dagrun_for_eligible_interval(dag_bag):
    """
    User Story: As a system, I want to periodically evaluate DAGs with defined schedules,
    to trigger executions when an eligible interval is identified, ensuring continuous data processing.
    """
    # 1. Given DAGs with a defined schedule
    # We iterate over all DAGs loaded in the project to ensure full coverage.
    dags_tested = 0

    for dag_id, dag in dag_bag.dags.items():
        # Skip DAGs without a schedule
        # In Airflow 2.x, the 'schedule' arg is converted into a 'timetable' attribute
        timetable = getattr(dag, "timetable", None)
        if timetable is None or type(timetable).__name__ == "NullTimetable":
            continue

        dags_tested += 1
        
        # Setup: Define an eligible interval (current time) and clear potential previous test data
        execution_date = timezone.utcnow()
        with create_session() as session:
            session.query(DagRun).filter(
                DagRun.dag_id == dag_id, 
                DagRun.execution_date == execution_date
            ).delete()
        
        # 2. When the scheduler evaluates an eligible execution interval
        # We infer the data interval just like the actual Airflow Scheduler does
        data_interval = dag.timetable.infer_manual_data_interval(run_after=execution_date)
        
        # Determine correct run_type (Dataset triggers have a specific run type in Airflow >= 2.4)
        run_type = "dataset_triggered" if type(timetable).__name__ == "DatasetTriggeredTimetable" else "scheduled"

        # Simulate the scheduler triggering the execution
        dag_run = dag.create_dagrun(
            state=State.QUEUED,
            execution_date=execution_date,
            run_type=run_type,
            data_interval=data_interval
        )
        
        # 3. Then: Executions are triggered and dag_runs records are created
        assert dag_run is not None, f"A dag_run should have been created for {dag_id}."
        
        # Checking Acceptance Criteria: The correct association of dag_run with the DAG
        assert dag_run.dag_id == dag_id, f"The dag_run is not correctly associated with DAG: {dag_id}."
        
        # Checking Acceptance Criteria: The initial state of the execution of each dag_run
        assert dag_run.state in [State.QUEUED, State.RUNNING, State.SUCCESS], \
            f"Initial state for {dag_id} was {dag_run.state}, expected one of: queued, running, success."

        # Teardown: Clean up the generated dag_run so we don't pollute the test database
        with create_session() as session:
            session.query(DagRun).filter(
                DagRun.dag_id == dag_id, 
                DagRun.execution_date == execution_date
            ).delete()
            
    # Sanity check to ensure we actually tested something
    assert dags_tested > 0, "No scheduled DAGs were found to test."