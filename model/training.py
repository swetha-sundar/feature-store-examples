from datetime import datetime
from feast import FeatureStore
import pandas as pd

#Configuration
bureau_fs = FeatureStore(repo_path="./feature_repo")
customer_fs = FeatureStore(repo_path="./another_feature_repo")


feature_service = bureau_fs.get_feature_service("risk_model_bureau_fs")

cust_features = [ #all from one feature registry only
    "customer_info_view:EXT_SOURCE_1",
    "customer_info_view:EXT_SOURCE_2",
    "customer_info_view:EXT_SOURCE_3",
]

entity_df = pd.DataFrame.from_dict(
    {
        "SK_ID_CURR": [100002, 100003, 100004],
        "label": [1, 0, 1],
        "event_timestamp": [
            datetime(2022,2,24),
            datetime(2022,2,24),
            datetime(2022,2,24),
        ],
    }
)

# bureau_df = bureau_fs.get_historical_features(
#     entity_df=entity_df,
#     features=feature_service
# ).to_df()

# print(bureau_df.head(5))

# customer_df = customer_fs.get_historical_features(
#     entity_df=entity_df,
#     features=cust_features
# ).to_df()

# print(customer_df.head(5))


##Get all features from registry

all_features = [
    "customer_info_view:EXT_SOURCE_1",
    "customer_info_view:EXT_SOURCE_2",
    "customer_info_view:EXT_SOURCE_3",
    "bureau_feature_view:DEBT_CREDIT_RATIO",
    "previous_loan_feature_view:AMT_BALANCE",
]

training_df = customer_fs.get_historical_features(
    entity_df=entity_df,
    features=all_features
).to_df()

print(training_df.head(5))