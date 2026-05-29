"""
Test Suite: Task Execution Isolation

User Story: As a developer, I want to execute tasks individually, 
to validate their logic without the need to execute the entire DAG.

This suite dynamically discovers all DAGs and Tasks, categorizing them into
different execution strategies (Check, Extract, Transform, Load). 
It uses Mocks to isolate tasks from external dependencies (network, database, 
heavy file I/O) ensuring fast and reliable unit testing.
"""
import pytest
import subprocess
from unittest import mock
from airflow.models import DagBag, TaskInstance, DagRun
from airflow.utils import timezone
from airflow.utils.state import State
from airflow.utils.session import create_session

# Load DAGs dynamically at pytest collection time
dag_bag_instance = DagBag(include_examples=False)

@pytest.fixture(scope="module")
def dag_bag():
    return dag_bag_instance

CHECK_TASKS = []
OSM_EXTRACT_TASKS = []
GOV_EXTRACT_TASKS = []
GOV_TRANSFORM_TASKS = []
LOAD_TASKS = []

for dag_id, dag in dag_bag_instance.dags.items():
    for task_id in dag.task_ids:
        if 'check_dependency' in task_id or 'check_geofabrik' in task_id:
            CHECK_TASKS.append((dag_id, task_id))
        elif 'extract_and_transform' in task_id:
            OSM_EXTRACT_TASKS.append((dag_id, task_id))
        elif task_id.startswith('extract_') and 'transform' not in task_id:
            GOV_EXTRACT_TASKS.append((dag_id, task_id))
        elif task_id.startswith('transform_'):
            GOV_TRANSFORM_TASKS.append((dag_id, task_id))
        elif task_id.startswith('load_'):
            LOAD_TASKS.append((dag_id, task_id))

def _run_isolated_task(dag_id, task_id, dag_bag):
    """
    Helper function to abstract the creation and isolated execution of a TaskInstance.
    """
    dag = dag_bag.get_dag(dag_id)
    assert dag is not None, f"DAG '{dag_id}' not found."
    
    task = dag.get_task(task_id)
    assert task is not None, f"Task '{task_id}' not found in DAG '{dag_id}'."
    
    execution_date = timezone.utcnow()
    
    with create_session() as session:
        session.query(DagRun).filter(
            DagRun.dag_id == dag_id,
            DagRun.execution_date == execution_date
        ).delete()
        
        data_interval = dag.timetable.infer_manual_data_interval(run_after=execution_date)
        dag_run = dag.create_dagrun(
            state=State.RUNNING,
            execution_date=execution_date,
            run_type="manual",
            session=session,
            data_interval=data_interval
        )
        
        ti = TaskInstance(task=task, run_id=dag_run.run_id)
        
        ti.run(ignore_all_deps=True, ignore_ti_state=True, test_mode=True, session=session)
        
        final_state = ti.state
        session.query(DagRun).filter(DagRun.run_id == dag_run.run_id).delete()
        
    return final_state


# =====================================================================
# Test Cases
# =====================================================================

@pytest.mark.parametrize("dag_id, task_id", CHECK_TASKS)
def test_check_dependency_tasks(dag_id, task_id, dag_bag):
    with mock.patch('os.path.exists', return_value=True):
        state = _run_isolated_task(dag_id, task_id, dag_bag)
        assert state == State.SUCCESS, f"Failed dependency check for {task_id} in {dag_id}"


@pytest.mark.parametrize("dag_id, task_id", OSM_EXTRACT_TASKS)
@mock.patch('shutil.which', return_value='/usr/bin/osmium')
@mock.patch('os.makedirs')
@mock.patch('subprocess.run')
@mock.patch('builtins.open', new_callable=mock.mock_open, read_data='{"features": []}')
def test_osm_extract_and_transform_tasks(mock_open, mock_subproc, mock_makedirs, mock_which, dag_id, task_id, dag_bag):
    state = _run_isolated_task(dag_id, task_id, dag_bag)
    assert state == State.SUCCESS, f"OSM Extraction failed for task {task_id} in {dag_id}"


@pytest.mark.parametrize("dag_id, task_id", GOV_EXTRACT_TASKS)
@mock.patch('requests.get')
@mock.patch('zipfile.ZipFile')
@mock.patch('os.makedirs')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_gov_extract_tasks(mock_open, mock_makedirs, mock_zipfile, mock_requests, dag_id, task_id, dag_bag):
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"fake_data"]
    mock_requests.return_value = mock_response
    state = _run_isolated_task(dag_id, task_id, dag_bag)
    assert state == State.SUCCESS, f"Gov Extraction failed for task {task_id} in {dag_id}"


@pytest.mark.parametrize("dag_id, task_id", GOV_TRANSFORM_TASKS)
@mock.patch('geopandas.read_file')
@mock.patch('os.walk', return_value=[('/tmp/fake', [], ['fake.shp'])])
@mock.patch('builtins.open', new_callable=mock.mock_open)
@mock.patch.object(TaskInstance, 'xcom_pull', return_value='/tmp/fake')
def test_gov_transform_tasks(mock_xcom, mock_open, mock_walk, mock_read_file, dag_id, task_id, dag_bag):
    import geopandas as gpd
    from shapely.geometry import Point
    mock_read_file.return_value = gpd.GeoDataFrame({
        'geometry': [Point(0, 0)],
        'CD_MUN': ['1234567'],
        'NM_MUN': ['Dummy City'],
        'SIGLA_UF': ['XX'],
        'CD_UF': ['12'],
        'NM_UF': ['Dummy State']
    }, crs="EPSG:4674")
    state = _run_isolated_task(dag_id, task_id, dag_bag)
    assert state == State.SUCCESS, f"Gov Transform failed for task {task_id} in {dag_id}"


@pytest.mark.parametrize("dag_id, task_id", LOAD_TASKS)
@mock.patch('airflow.providers.postgres.hooks.postgres.PostgresHook')
@mock.patch('builtins.open', new_callable=mock.mock_open, read_data='[]')
@mock.patch.object(TaskInstance, 'xcom_pull', return_value='/tmp/dummy.json')
def test_load_tasks(mock_xcom, mock_open, mock_hook, dag_id, task_id, dag_bag):
    # Mocking PostgresHook totally shields the actual database from TRUNCATE/INSERT operations
    state = _run_isolated_task(dag_id, task_id, dag_bag)
    assert state == State.SUCCESS, f"Load failed for task {task_id} in {dag_id}"
    
    
@mock.patch('os.path.exists', return_value=True)
@mock.patch('subprocess.run')
def test_update_osm_diffs_task(mock_subproc, mock_exists, dag_bag):
    # Mock the return values of the pyosmium terminal output to trick Airflow into a success path
    mock_subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='ok', stderr='')
    state = _run_isolated_task('update_osm_diffs', 'update_osm_diffs', dag_bag)
    assert state == State.SUCCESS, "Update OSM diffs task failed"


# Dynamic fallback to test the download DAG if it exists in your directory
def test_download_geofabrik_data_task(dag_bag):
    dag_id = 'download_geofabrik_data'
    if dag_id in dag_bag.dags:
        task_id = dag_bag.dags[dag_id].task_ids[0]
        with mock.patch('subprocess.run') as mock_subproc, \
             mock.patch('os.makedirs'), \
             mock.patch('os.rename'), \
             mock.patch('requests.get') as mock_requests, \
             mock.patch('urllib.request.urlretrieve'), \
             mock.patch('builtins.open', new_callable=mock.mock_open):
            
            mock_subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='ok', stderr='')
            
            mock_response = mock.Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [b"fake_data"]
            mock_requests.return_value = mock_response
            
            state = _run_isolated_task(dag_id, task_id, dag_bag)
            assert state == State.SUCCESS, f"Download task failed in {dag_id}"