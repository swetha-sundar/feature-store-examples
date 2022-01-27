from datetime import datetime, timedelta
import pandas as pd
from feast import FeatureStore
import yaml

fs = FeatureStore(repo_path=".")
database = yaml.safe_load(open("feature_store.yaml"))["offline_store"]["database"]

# Select features
features = ["driver_hourly_stats:conv_rate",
            "driver_hourly_stats:acc_rate",
            "driver_hourly_stats:avg_daily_trips",
            "customer_stats:current_balance",
            "customer_stats:avg_passenger_count",
            "customer_stats:lifetime_trip_count"]

# Create an entity dataframe. This is the dataframe that will be enriched with historical features
entity_df = pd.DataFrame(
    {
        "event_timestamp": [
            pd.Timestamp(dt, unit="ms", tz="UTC").round("ms")
            for dt in pd.date_range(
                start=datetime.now() - timedelta(days=101),
                end=datetime.now() - timedelta(days=99),
                periods=3,
            )
        ],
        "driver_id": [50893, 50441, 50283],
        "customer_id": [20311, 20423, 20428]
    }
)

# Retrieve historical features by joining the entity dataframe to the Snowflake table source
print("Retrieving training data...")
training_df = fs.get_historical_features(
    features=features,
    entity_df=entity_df
).to_df()
print(training_df)
