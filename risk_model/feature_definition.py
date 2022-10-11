from datetime import timedelta
from feast import Entity
from feast import Feature
from feast import FeatureStore
from feast import FeatureService
from feast import FeatureView
from feast import SnowflakeSource
from feast import ValueType
from google.protobuf.json_format import MessageToDict
import yaml

# Configuration
repo_path = "."
fs = FeatureStore(repo_path)
config_path = repo_path + "/feature_store.yaml"
database_name = yaml.safe_load(open(config_path))["offline_store"]["database"]

print("Database Source: ", database_name)
print("\n")
##
# Source Data
##
bureau_feature_table = SnowflakeSource(
    database=database_name,
    schema="PUBLIC",
    table="BUREAU_FEATURE_TABLE",
    event_timestamp_column="EVENT_TIMESTAMP",
)

previous_loan_feature_table = SnowflakeSource(
    database=database_name,
    schema="PUBLIC",
    table="PREVIOUS_LOAN_FEATURES_TABLE",
    event_timestamp_column="EVENT_TIMESTAMP",
)

customer_info_table = SnowflakeSource(
    database=database_name,
    schema="PUBLIC",
    table="STATIC_FEATURES_TABLE",
    event_timestamp_column="EVENT_TIMESTAMP",
)

# Entity definition
customer = Entity(name="SK_ID_CURR", value_type=ValueType.INT64,
                  description="customer id",)

# Feature View(s) definition
bureau_view = FeatureView(
    name="bureau_feature_view",
    entities=["SK_ID_CURR"],
    ttl=timedelta(days=100),
    online=True,
    batch_source=bureau_feature_table,
    tags={},
)

previous_loan_view = FeatureView(
    name="previous_loan_feature_view",
    entities=["SK_ID_CURR"],
    ttl=timedelta(days=100),
    online=True,
    batch_source=previous_loan_feature_table,
    tags={},
)

# Feature Service Definition
credit_risk_model_fs = FeatureService(
    name="credit_risk_model_fs",
    features=[bureau_view, previous_loan_view[["AMT_BALANCE"]]]
)

# Feature Registration
fs.apply([customer, bureau_view, previous_loan_view, credit_risk_model_fs])

# List features from registry
print("====FEATURE VIEWS====")
fv_list = fs.list_feature_views()
for fv in fv_list:
    d = MessageToDict(fv.to_proto())
    print("Feature View Name:", d['spec']['name'])
    print("Entities:", d['spec']['entities'])
    print("Features:", d['spec']['features'])
    print("Source Type:", d['spec']['batchSource']['dataSourceClassType'])
    print("\n")

print("====FEATURE SERVICE====")
fs_list = fs.list_feature_services()
for fserv in fs_list:
    d = MessageToDict(fserv.to_proto())
    print("Feature Service Name:", d['spec']['name'])
    print("Feature Views:", d['spec']['features'])
    print("\n")
