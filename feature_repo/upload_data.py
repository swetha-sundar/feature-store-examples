from feast_snowflake.snowflake_utils import create_new_snowflake_table, get_snowflake_conn
from snowflake.connector.pandas_tools import write_pandas
from feast import FeatureStore
import pandas as pd

fs = FeatureStore(repo_path=".")

with get_snowflake_conn(fs.config.offline_store) as conn:

  create_new_snowflake_table(conn, pd.read_parquet('data/driver_stats.parquet'), 'DRIVER_STATS')
  write_pandas(conn, pd.read_parquet('data/driver_stats.parquet'), 'DRIVER_STATS')
  create_new_snowflake_table(conn, pd.read_csv('data/customer_profile.csv'), 'CUSTOMER_STATS')
  write_pandas(conn, pd.read_csv('data/customer_profile.csv'), 'CUSTOMER_STATS')
  create_new_snowflake_table(conn, pd.read_csv('data/orders.csv'), 'ORDER_STATS')
  write_pandas(conn, pd.read_csv('data/orders.csv'), 'ORDER_STATS')
  create_new_snowflake_table(conn, pd.read_csv('data/driver_hourly.csv'), 'DRIVER_HOURLY_STATS')
  write_pandas(conn, pd.read_csv('data/driver_hourly.csv'), 'DRIVER_HOURLY_STATS')
