from datetime import timedelta
import os
import yaml

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from feast import Entity
from feast import Feature
from feast import FeatureStore
from feast import FeatureService
from feast import FeatureView
from feast import SnowflakeSource
from feast import ValueType
from google.protobuf.json_format import MessageToDict

# Get Keyvault name
keyVaultName = os.environ["KEY_VAULT_NAME"]
KVUri = f"https://{keyVaultName}.vault.azure.net"

# Get Azure credentials
USER_MSI_CLIENT_ID=os.environ["USER_MSI_CLIENT_ID"]
credential = DefaultAzureCredential(managed_identity_client_id=USER_MSI_CLIENT_ID)

# Get Azure Key Vault Client
kv = SecretClient(vault_url=KVUri, credential=credential)

# Get and set snowflake access credentials as environment variable
os.environ['SNOWFLAKE_USER'] = kv.get_secret("SNOWFLAKE-USER").value
os.environ['SNOWFLAKE_PASS'] = kv.get_secret("SNOWFLAKE-PASS").value
os.environ['SNOWFLAKE_ACC'] = kv.get_secret("SNOWFLAKE-ACC").value
os.environ['REGISTRY_PATH'] = kv.get_secret("REGISTRY-PATH").value

# Feast Configuration
repo_path = "./config"
fs = FeatureStore(repo_path)
config_path = repo_path + "/feature_store.yaml"
database_name = yaml.safe_load(open(config_path))["offline_store"]["database"]

print("Database Source: ", database_name)
print("\n")
##
###Source Data (Feature Values)
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

#Entity definition
customer =  Entity(name="SK_ID_CURR", value_type=ValueType.INT64, description="customer id",)

#Feature View(s) definition
bureau_view = FeatureView(
    name="bureau_feature_view",
    entities=["SK_ID_CURR"],
    ttl=timedelta(days=100),
    online=False,
    batch_source=bureau_feature_table,
    tags={},
)

previous_loan_view = FeatureView(
    name="previous_loan_feature_view",
    entities=["SK_ID_CURR"],
    ttl=timedelta(days=100),
    online=False,
    batch_source=previous_loan_feature_table,
    tags={},
)

#Feature View definition
customer_view = FeatureView(
    name="customer_info_view",
    entities=["SK_ID_CURR"],
    ttl=timedelta(days=100),
    features=[
        Feature(name="OCCUPATION_TYPE", dtype=ValueType.STRING),
        Feature(name="AMT_INCOME_TOTAL", dtype=ValueType.FLOAT),
        Feature(name="NAME_INCOME_TYPE", dtype=ValueType.STRING),
        Feature(name="DAYS_LAST_PHONE_CHANGE", dtype=ValueType.FLOAT),
        Feature(name="ORGANIZATION_TYPE", dtype=ValueType.STRING),
        Feature(name="AMT_CREDIT", dtype=ValueType.FLOAT),
        Feature(name="AMT_GOODS_PRICE", dtype=ValueType.FLOAT),
        Feature(name="DAYS_REGISTRATION", dtype=ValueType.FLOAT),
        Feature(name="AMT_ANNUITY", dtype=ValueType.FLOAT),
        Feature(name="CODE_GENDER", dtype=ValueType.STRING),
        Feature(name="DAYS_ID_PUBLISH", dtype=ValueType.INT64),
        Feature(name="NAME_EDUCATION_TYPE", dtype=ValueType.STRING),
        Feature(name="DAYS_EMPLOYED", dtype=ValueType.INT64),
        Feature(name="DAYS_BIRTH", dtype=ValueType.INT64),
        Feature(name="EXT_SOURCE_1", dtype=ValueType.FLOAT),
        Feature(name="EXT_SOURCE_2", dtype=ValueType.FLOAT),
        Feature(name="EXT_SOURCE_3", dtype=ValueType.FLOAT),
    ],

    online=False,
    batch_source=customer_info_table,
    tags={},
)

#Feature Service Definition
risk_model_bureau_fs = FeatureService(
    name="risk_model_fs",
    features=[bureau_view, previous_loan_view]
)

#Feature Registration
fs.apply([customer, bureau_view, previous_loan_view, customer_view, risk_model_bureau_fs])

# List features from registry
print("====FEATURE VIEWS====")
fv_list = fs.list_feature_views()
for fv in fv_list:
    d=MessageToDict(fv.to_proto())
    print("Feature View Name:", d['spec']['name'])
    print("Entities:", d['spec']['entities'])
    print("Features:", d['spec']['features'])
    print("Source Type:", d['spec']['batchSource']['dataSourceClassType'])
    print("\n")

print("====FEATURE SERVICE====")
fs_list = fs.list_feature_services()
for fserv in fs_list:
    d=MessageToDict(fserv.to_proto())
    print("Feature Service Name:", d['spec']['name'])
    print("Feature Views:", d['spec']['features'])
    print("\n")