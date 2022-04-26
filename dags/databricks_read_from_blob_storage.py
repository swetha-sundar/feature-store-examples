from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.utils.dates import days_ago

default_args = {
  'owner': 'merlion_crew'
}

with DAG('databricks_dag',
  start_date = days_ago(2),
  schedule_interval = None,
  default_args = default_args
  ) as dag:

  opr_run_now = DatabricksRunNowOperator(
    task_id = 'read_from_blob_storage',
    databricks_conn_id = 'databricks_default',
    job_id = 91
  )
