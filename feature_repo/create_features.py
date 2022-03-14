# This is an example feature definition file
from datetime import timedelta
from html import entities
from feast import Entity, Feature, FeatureView, FeatureStore, SnowflakeSource, ValueType
import pandas as pd
from google.protobuf.json_format import MessageToDict
import yaml


fs = FeatureStore(repo_path=".")

# Read data from Snowflake table
# Here we use a Table to reuse the original parquet data,
# but you can replace to your own Table or Query.
database = yaml.safe_load(open("feature_store.yaml"))["offline_store"]["database"]

driver_stats = SnowflakeSource(
    database="{database}",
    schema="PUBLIC",
    table="DRIVER_STATS",
    #query = """ """,
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created",
)

driver_hourly_stats = SnowflakeSource(
    database="{database}",
    schema="PUBLIC",
    table="DRIVER_HOURLY_STATS",
    event_timestamp_column="datetime",
    created_timestamp_column="created",
)

customer_stats = SnowflakeSource(
    database="{database}",
    schema="PUBLIC",
    table="CUSTOMER_STATS",
    event_timestamp_column="datetime",
    created_timestamp_column="created",
)

# Define Features
conv_rate = Feature(name="conv_rate", dtype=ValueType.FLOAT)
acc_rate = Feature(name="acc_rate", dtype=ValueType.FLOAT)
avg_daily_trips = Feature(name="avg_daily_trips", dtype=ValueType.INT64)

current_balance = Feature(name="current_balance", dtype=ValueType.FLOAT)
avg_passenger_count = Feature(name="avg_passenger_count", dtype=ValueType.FLOAT)
lifetime_trip_count = Feature(name="lifetime_trip_count", dtype=ValueType.INT32)

# Define FeatureView
driver_hourly_stats_view = FeatureView(
    name="driver_hourly_stats",
    entities=["driver_id"],
    ttl=timedelta(hours=2),
    features=[
        acc_rate,
        conv_rate,
        avg_daily_trips
    ],
    online=True,
    batch_source=driver_hourly_stats,
    tags={},
)

customer_stats_view = FeatureView(
    name="customer_stats",
    entities=["customer_id"],
    ttl=timedelta(days=4),
    features=[
        current_balance,
        avg_passenger_count,
        lifetime_trip_count
    ],
    batch_source=customer_stats,
    online=True,
    tags={},
)

# Define entities
driver = Entity(name="driver_id", value_type=ValueType.INT64, description="driver identifier", join_key="driver_id")
customer = Entity(name = "customer_id", value_type=ValueType.INT64, description="customer_identifier")

fs.apply([driver, driver_hourly_stats_view, customer, customer_stats_view])

# List features from registry

for f in fs.list_feature_views():
    d=MessageToDict(f.to_proto())
    print("Feature View Name:", d['spec']['name'])
    print("Entities:", d['spec']['entities'])
    print("Features:", d['spec']['features'])
    print("Source Type:", d['spec']['batchSource']['dataSourceClassType'])
    print("\n")