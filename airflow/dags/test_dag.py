
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="test",
    start_date=datetime(2024,1,1),
    schedule="@daily",
    catchup=False
) as dag:

    task = BashOperator(
        task_id="hello",
        bash_command="echo hello"
    )