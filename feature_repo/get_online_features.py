from datetime import datetime, timedelta
from feast import FeatureStore

fs = FeatureStore(repo_path=".")

# print("Loading features into the online store...")
stime=datetime.now() - timedelta(days=110)
etime=datetime.now() - timedelta(days=100)
fs.materialize_incremental(end_date=etime)

# Select features
features = ["driver_hourly_stats:conv_rate",
            "driver_hourly_stats:acc_rate",
            "driver_hourly_stats:avg_daily_trips",
            ]

# Retrieve features from the online store
print("Retrieving online features...")
online_features = fs.get_online_features(
    features=features,
    entity_rows=[{"driver_id": 50893}, {"driver_id": 50091}],
).to_dict()
print(online_features)