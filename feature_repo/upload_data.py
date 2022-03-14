from feast.infra.utils.snowflake_utils import (
    get_snowflake_conn,
    write_pandas,
)
from snowflake.connector.pandas_tools import write_pandas
from feast import FeatureStore
import pandas as pd

fs = FeatureStore(repo_path=".")

with get_snowflake_conn(fs.config.offline_store) as conn:

  write_pandas(conn, pd.read_parquet('data/driver_stats.parquet'), 'DRIVER_STATS', auto_create_table=True)
  write_pandas(conn, pd.read_csv('data/customer_profile.csv'), 'CUSTOMER_STATS',  auto_create_table=True)
  write_pandas(conn, pd.read_csv('data/orders.csv'), 'ORDER_STATS',  auto_create_table=True)
  write_pandas(conn, pd.read_csv('data/driver_hourly.csv'), 'DRIVER_HOURLY_STATS',   auto_create_table=True)
