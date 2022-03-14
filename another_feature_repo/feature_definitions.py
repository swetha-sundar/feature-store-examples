from datetime import timedelta
from feast import Entity
from feast import Feature
from feast import FeatureStore
from feast import FeatureView
from feast import SnowflakeSource
from feast import ValueType
from google.protobuf.json_format import MessageToDict
import yaml

#Configuration
repo_path = "./another_feature_repo"
fs = FeatureStore(repo_path)
config_path = repo_path + "/feature_store.yaml"
database_name = yaml.safe_load(open(config_path))["offline_store"]["database"]
print("DATABASE SOURCE:", database_name)
print("\n")

#Source Data
customer_info_table = SnowflakeSource(
    database=database_name,
    schema="PUBLIC",
    table="STATIC_FEATURES_TABLE",
    event_timestamp_column="EVENT_TIMESTAMP",
)

#Entity definition
customer =  Entity(name="SK_ID_CURR", value_type=ValueType.INT64, description="customer id",)

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

#Feature Registration
fs.apply([customer, customer_view])

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
