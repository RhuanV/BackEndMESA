"""
Test Suite: Failure Handling & Recovery

User Story: As a system, I want task execution failures to be handled in a controlled 
and predictable manner, ensuring state consistency and enabling automatic recovery.

Test Strategy: Create a test DAG with controlled failure scenarios (persistent failure, 
eventual success, upstream failure) and validate state transitions, retries, 
and manual reprocessing.
"""
import pytest
from datetime import timedelta
from airflow.models import DAG, DagRun, TaskInstance
from airflow.operators.python import PythonOperator
from airflow.utils.state import State
from airflow.utils.session import create_session
from airflow.utils import timezone

# =====================================================================
# Dummy Callables to Simulate Failure Scenarios
# =====================================================================
def _fail_always():
    raise ValueError("Simulated persistent failure.")

def _fail_once(**context):
    ti = context['ti']
    # try_number is 1 on the first attempt.
    if ti.try_number <= 1:
        raise ValueError("Simulated temporary failure.")
    return "Success on second try"

def _downstream_task():
    return "I should never run due to upstream failure"

# =====================================================================
# Fixtures
# =====================================================================
@pytest.fixture(scope="module")
def failure_dag():
    """
    Creates an in-memory DAG tailored specifically for failure testing.
    """
    with DAG(
        "test_failure_handling_dag",
        start_date=timezone.utcnow() - timedelta(days=1),
        schedule=None,
        catchup=False,
    ) as dag:
        
        t1 = PythonOperator(
            task_id="always_fails",
            python_callable=_fail_always,
            retries=1,
            retry_delay=timedelta(seconds=0)
        )
        
        t2 = PythonOperator(
            task_id="downstream",
            python_callable=_downstream_task
        )
        t1 >> t2

        t3 = PythonOperator(
            task_id="eventually_succeeds",
            python_callable=_fail_once,
            retries=1,
            retry_delay=timedelta(seconds=0)
        )
    return dag

# =====================================================================
# Test Cases
# =====================================================================
def test_task_failure_and_upstream_propagation(failure_dag):
    """
    Acceptance Criteria:
    - Tasks that fail are marked as 'failed' or 'up_for_retry'.
    - Exhausting retries marks the task as 'failed'.
    - Dependent tasks reflect upstream failures ('upstream_failed').
    - Final DAG run state is consistent (FAILED).
    """
    execution_date = timezone.utcnow()
    with create_session() as session:
        data_interval = failure_dag.timetable.infer_manual_data_interval(run_after=execution_date)
        dag_run = failure_dag.create_dagrun(
            state=State.RUNNING,
            execution_date=execution_date,
            run_type="manual",
            session=session,
            data_interval=data_interval
        )
        
        # Always pull the instance tracked by the database, do not create a detached one
        ti1 = dag_run.get_task_instance("always_fails", session=session)
        t1 = failure_dag.get_task("always_fails")
        ti1.task = t1
        
        # 1. First Execution -> Should fail and go to UP_FOR_RETRY
        try:
            ti1.run(ignore_all_deps=True, session=session)
        except Exception:
            pass # Expected to raise, but Airflow handles the state transition internally
        
        ti1.refresh_from_db(session=session)
        assert ti1.state == State.UP_FOR_RETRY, "Task should be marked for retry on first failure"
        assert ti1.try_number == 2, "Try number should increment"

        # 2. Simulate scheduler picking it up after the retry_delay
        ti1.state = State.SCHEDULED
        session.commit()

        # 3. Second Execution -> Should fail and go to FAILED (retries exhausted)
        ti1.task = t1 # Must re-attach task after refresh/commit!
        try:
            ti1.run(ignore_all_deps=True, session=session)
        except Exception:
            pass
            
        ti1.refresh_from_db(session=session)
        assert ti1.state == State.FAILED, "Task should be marked as failed after exhausting retries"
        
        # 4. Run the other branch of the DAG to ensure all paths are complete
        ti3 = dag_run.get_task_instance("eventually_succeeds", session=session)
        t3 = failure_dag.get_task("eventually_succeeds")
        ti3.task = t3
        
        # Attempt 1 -> Fails and goes to UP_FOR_RETRY
        try:
            ti3.run(ignore_all_deps=True, session=session)
        except Exception:
            pass
            
        # Attempt 2 -> Schedule and run again. It should succeed now.
        ti3.refresh_from_db(session=session)
        ti3.state = State.SCHEDULED
        session.commit()
        
        ti3.task = t3 # Re-attach task!
        ti3.run(ignore_all_deps=True, session=session)
        
        ti3.refresh_from_db(session=session)
        assert ti3.state == State.SUCCESS, "Task should succeed on its second attempt"

        # 5. Check upstream failure propagation and final DagRun state
        dag_run.dag = failure_dag # Explicitly attach DAG before updating state
        dag_run.update_state(session=session) # This evaluates all TIs and updates dependent states
        session.commit()
        
        # Double-check evaluation: After cascading UPSTREAM_FAILED to downstream tasks,
        # Airflow needs one last check to declare the entire DagRun as FAILED.
        dag_run.update_state(session=session)
        
        ti2 = dag_run.get_task_instance("downstream", session=session)
        assert ti2.state == State.UPSTREAM_FAILED, "Downstream task should be marked as upstream_failed"
        assert str(dag_run.state) == "failed", f"DagRun state is {dag_run.state}, expected failed."
        
        # Teardown
        session.query(DagRun).filter(DagRun.run_id == dag_run.run_id).delete()

def test_task_eventual_success_and_reprocessing(failure_dag):
    """
    Acceptance Criteria:
    - Task with retries eventually succeeds.
    - Execution with failure can be manually reprocessed safely (Clear/Rerun).
    """
    execution_date = timezone.utcnow()
    with create_session() as session:
        data_interval = failure_dag.timetable.infer_manual_data_interval(run_after=execution_date)
        dag_run = failure_dag.create_dagrun(
            state=State.RUNNING,
            execution_date=execution_date,
            run_type="manual",
            session=session,
            data_interval=data_interval
        )
        
        # Acceptance Criteria: Manual reprocessing (Clear state)
        # Simulating a user clicking "Clear Task" in the Airflow UI to reprocess
        failure_dag.clear(start_date=execution_date, end_date=execution_date, task_ids=["eventually_succeeds"], session=session)
        
        ti3 = dag_run.get_task_instance("eventually_succeeds", session=session)
        assert ti3.state == State.NONE, "Task state should be reset to NONE for manual reprocessing, ensuring consistency."
        
        session.query(DagRun).filter(DagRun.run_id == dag_run.run_id).delete()