"""
## Model Training in Azure ML with FEAST as Feature Store
- This script performs Model Training and Registration by building the train/test dataset using features from Feast Feature Store
  - Feast for Feature Store
  - Uses Azure Storage Account
  - Uses Azure ML Model Registry

### Prerequisites
- Ensure  **Feature Definitions and Feature Registrations** pertaining to the Home Credit Risk Default usecase is executed. Registry is created
"""

from datetime import datetime
import lightgbm as lgb
import mlflow
import os
import pandas as pd
import pickle
import traceback

from sklearn import metrics
from sklearn.model_selection import train_test_split

from azureml.core.model import Model
from azureml.core.run import Run

from feast import FeatureStore
from feast import RepoConfig
from feast.infra.offline_stores.snowflake import SnowflakeOfflineStoreConfig
from feast.infra.online_stores.redis import RedisOnlineStoreConfig
from feast.registry import RegistryConfig

import snowflake.connector as snow


def get_entities_snowflake(snowflake_creds, entity_sql_query):
    print("===Get Entity Dataframe===")
    # Snowflake python connector to populate data from datasource to table in snowflake and query from snowflake
    conn = snow.connect(
        user=snowflake_creds["SNOWFLAKE_USER"],
        password=snowflake_creds["SNOWFLAKE_PASS"],
        account=snowflake_creds["SNOWFLAKE_ACC"],
        warehouse=snowflake_creds["SNOWFLAKE_COMPUTE"],
        database=snowflake_creds["SNOWFLAKE_DB"],
        schema="PUBLIC"
    )
    # fetch table from snowflake as pandas
    cur = conn.cursor()
    sql = entity_sql_query
    cur.execute(sql)
    id_train = cur.fetch_pandas_all()
    cur.close()
    return id_train


def get_features_feast(id_train, datearray, feature_service_name):
    """ Fetch features from registry for the entities from snowflake for a specified time period

    Parameters
    ----------
    id_train : Pandas<dataframe>
    datearray: datetime array
    feature_service_name: str

    Returns
    -------
    Pandas<dataframe>
        Training data for model training is returned
    """
    print("===Get Features data===")
    # create entity df from id_train
    entity_df = pd.DataFrame.from_dict(
        {
            "SK_ID_CURR": id_train['SK_ID_CURR'].tolist(),
            "TARGET": id_train['TARGET'].tolist(),
            "event_timestamp": datearray*id_train.shape[0]
        }
    )
    # use feature service of this model
    feature_service = fs.get_feature_service(feature_service_name)

    # get data from snowflake based on entity_df and feature service
    features_df = fs.get_historical_features(
        entity_df=entity_df,
        features=feature_service).to_df()

    return features_df


def drop_target(train_df, primary_key, target_key):
    # drop id and timestamp
    train_df = train_df.sort_values(by=primary_key)
    train_df = train_df.drop(columns=['event_timestamp', primary_key])

    # Isolate target column
    y = train_df[target_key]
    X = train_df.drop(columns=[target_key])

    return X, y


def traintest_split(X, y):
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.6, random_state=42)
    X_test, X_valid, y_test, y_valid = train_test_split(
        X_test, y_test, test_size=0.5, random_state=42)

    print(len(X_train), len(y_train), sum(y_train))
    print(len(X_valid), len(y_valid), sum(y_valid))
    print(len(X_test), len(y_test), sum(y_test))

    return X_train, X_test, X_valid, y_train, y_test, y_valid


def train_model(X_train, X_test, X_valid, y_train, y_test, y_valid):

    os.makedirs('./outputs', exist_ok=True)
    mlflow.lightgbm.autolog()
    run = Run.get_context()

    model_name = 'lgbm_home_credit1'
    model = lgb.LGBMClassifier(
        objective="binary",
        n_estimators=1000,
        learning_rate=0.01,
        num_leaves=34,
        max_depth=9,
        random_state=42
    )
    model.fit(X_train, y_train,
              eval_set=[(X_valid, y_valid)],
              eval_metric=["AUC", "binary_logloss"],
              verbose=100,
              early_stopping_rounds=100
              )

    y_pred_proba = model.predict_proba(X_test)
    roc_auc = metrics.roc_auc_score(y_test, y_pred_proba[:, 1])
    print(f"ROC AUC score: {roc_auc:.2f}")
    # log metrics
    run.log('roc_auc', roc_auc)

    model_file_name = '{}.pkl'.format(model_name)
    model_path = './outputs/' + model_file_name
    with open(os.path.join('./outputs/', model_file_name), 'wb') as file:
        pickle.dump(model, file)
    register_aml_model(model_path, model_name, run.experiment, run.id)
    return model


def connect_feature_registry():
    global fs

    feast_registry_path = os.getenv("REGISTRY_PATH")
    snowflake_acc = os.getenv("SNOWFLAKE_ACC")
    snowflake_user = os.getenv("SNOWFLAKE_USER")
    snowflake_pass = os.getenv("SNOWFLAKE_PASS")
    snowflake_compute_name = os.getenv("SNOWFLAKE_COMPUTE_NAME")
    snowflake_database_name = os.getenv("SNOWFLAKE_DB_NAME")
    snowflake_role_name = os.getenv("SNOWFLAKE_ROLE_NAME")
    redis_conn_string = os.getenv("REDIS_CONN_STRING")

    print("connecting to registry...")
    reg_config = RegistryConfig(
        registry_store_type="feast_azure_provider.registry_store.AzBlobRegistryStore",
        path=feast_registry_path,
    )

    print("connecting to repo config...")
    repo_cfg = RepoConfig(
        project="dev",
        provider="feast_azure_provider.azure_provider.AzureProvider",
        registry=reg_config,
        offline_store=SnowflakeOfflineStoreConfig(
            account=snowflake_acc,
            user=snowflake_user,
            password=snowflake_pass,
            role=snowflake_role_name,
            database=snowflake_database_name,
            warehouse=snowflake_compute_name),
        online_store=RedisOnlineStoreConfig(
            connection_string=redis_conn_string),
    )

    print("connecting to feature store...")
    fs = FeatureStore(config=repo_cfg)


def register_aml_model(
    model_path,
    model_name,
    exp,
    run_id
):
    try:
        tagsValue = {"run_id": run_id,
                     "experiment_name": exp.name}

        model = Model.register(
            workspace=exp.workspace,
            model_name=model_name,
            model_path=model_path,
            tags=tagsValue)
        os.chdir("..")
        print(
            "Model registered: {} \nModel Description: {} "
            "\nModel Version: {}".format(
                model.name, model.description, model.version
            )
        )
    except Exception:
        traceback.print_exc(limit=None, file=None, chain=True)
        print("Model registration failed")
        raise


def main():

    # Getting training Data
    print("===Get Entities===")
    snow_creds = {"SNOWFLAKE_ACC": os.environ["SNOWFLAKE_ACC"],
                  "SNOWFLAKE_USER": os.environ["SNOWFLAKE_USER"],
                  "SNOWFLAKE_PASS": os.environ["SNOWFLAKE_PASS"],
                  "SNOWFLAKE_COMPUTE": os.environ["SNOWFLAKE_COMPUTE_NAME"],
                  "SNOWFLAKE_DB": os.environ["SNOWFLAKE_DB_NAME"]
                  }
    sql_query = 'select SK_ID_CURR, TARGET from  "TEST"."PUBLIC"."APPLICATION_TRAIN"'
    id_train = get_entities_snowflake(
        snowflake_creds=snow_creds, entity_sql_query=sql_query)
    print(id_train.info())
    datearray = [datetime(2022, 2, 24)]

    # Connect to Feast Feature Registry
    connect_feature_registry()
    train_df = get_features_feast(id_train, datearray, 'credit_risk_model_fs')
    print(train_df.info())

    # Preprocessing Data
    print("===Data Preprocessing===")

    # Drop Target Column
    X, y = drop_target(train_df, "SK_ID_CURR", "TARGET")

    # Train test split
    X_train, X_test, X_valid, y_train, y_test, y_valid = traintest_split(X, y)

    # Model Training
    print("===Model Training===")
    model = train_model(X_train, X_test, X_valid, y_train, y_test, y_valid)

    print("Model Training Done!")


if __name__ == '__main__':
    main()
