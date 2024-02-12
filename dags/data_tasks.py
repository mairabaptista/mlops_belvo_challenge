from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from utils.prepare_methods import read_data_from_s3, validate_data, prepare_data


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'demo_dag',
    default_args=default_args,
    description='Demo component for test',
    schedule_interval=timedelta(days=1),
)

read_data_task = PythonOperator(
    task_id='read_data',
    python_callable=read_data_from_s3,
    provide_context=True,
    dag=dag,
)

validate_data_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    op_kwargs={'df': "{{ task_instance.xcom_pull(task_ids='read_data') }}"},
    dag=dag,
)

prepare_data_task = PythonOperator(
    task_id='validate_data',
    python_callable=prepare_data,
    op_kwargs={'df': "{{ task_instance.xcom_pull(task_ids='validate_data') }}"},
    dag=dag,
)


read_data_task >> validate_data_task >> prepare_data_task
## remaining tasks for this component are not pictured in this example
## ml_training_task >> ml_evaluation_task >> ml_validation_task

