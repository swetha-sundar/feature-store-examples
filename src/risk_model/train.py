from datetime import datetime
import lightgbm as lgb
import mlflow
import os
import pandas as pd
import pickle
import traceback

from sklearn import metrics
from sklearn.model_selection import train_test_split

from azureml.core import Environment
from azureml.core.model import Model
from azureml.core.run import Run
from azureml.core import Workspace

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
        user = snowflake_creds["SNOWFLAKE_USER"],
        password = snowflake_creds["SNOWFLAKE_PASS"],
        account= snowflake_creds["SNOWFLAKE_ACC"],
        warehouse="COMPUTE_WH",
        database="HOME_CREDIT_DATA",
        schema="PUBLIC"
    )
    #fetch table from snowflake as pandas
    cur = conn.cursor()
    sql = entity_sql_query
    cur.execute(sql)
    id_train = cur.fetch_pandas_all()
    cur.close()
    return id_train


def get_features_feast(id_train, datearray, feature_service_name):

    print("===Get Features data===")

    # load features from Feast
    # repo_path = "./config" #Feast Feature Repo Path
    # fs = FeatureStore(repo_path)

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
    #drop id and timestamp
    train_df = train_df.sort_values(by=primary_key)
    train_df = train_df.drop(columns = ['event_timestamp', primary_key])

    #Isolate target column
    y = train_df[target_key]
    X = train_df.drop(columns = [target_key])

    return X, y

def traintest_split(X, y):
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.6, random_state=42)
    X_test, X_valid, y_test, y_valid = train_test_split(X_test, y_test, test_size=0.5, random_state=42)

    print(len(X_train), len(y_train), sum(y_train))
    print(len(X_valid), len(y_valid), sum(y_valid))
    print(len(X_test), len(y_test), sum(y_test))

    return X_train, X_test, X_valid, y_train, y_test, y_valid

def get_azureml_mlflow_tracking_uri(region, subscription_id, resource_group, workspace):
    return "azureml://{}.api.azureml.ms/mlflow/v1.0/subscriptions/{}/resourceGroups/{}/providers/Microsoft.MachineLearningServices/workspaces/{}".format(region, subscription_id, resource_group, workspace)

def train_model(X_train, X_test, X_valid, y_train, y_test, y_valid ):

    # region='centralus' ## example: westus
    # subscription_id = '371e8e7f-bce0-4db0-9df5-d88805b41101' ## example: 11111111-1111-1111-1111-111111111111
    # resource_group = 'mlops-RG' ## example: myresourcegroup
    # workspace = 'mlops-AML-WS' ## example: myworkspacename

    # MLFLOW_TRACKING_URI = get_azureml_mlflow_tracking_uri(region, subscription_id, resource_group, workspace)

    # ## Set the MLFLOW TRACKING URI
    # mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # ## Make sure the MLflow URI looks something like this:
    # ## azureml://<REGION>.api.azureml.ms/mlflow/v1.0/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.MachineLearningServices/workspaces/<AML_WORKSPACE_NAME>

    # print("MLFlow Tracking URI:", MLFLOW_TRACKING_URI)

    os.makedirs('./outputs', exist_ok=True)
    mlflow.lightgbm.autolog()
    run = Run.get_context()

    exp_name = 'lgbm_home_credit1'
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
            eval_metric=["AUC","binary_logloss"],
            verbose= 100,
            early_stopping_rounds= 100
    )

    y_pred_proba = model.predict_proba(X_test)
    roc_auc = metrics.roc_auc_score(y_test, y_pred_proba[:, 1])
    print(f"ROC AUC score: {roc_auc:.2f}")
    # log metrics
    run.log('roc_auc', roc_auc)
    # mlflow.log_metrics({"roc_auc": roc_auc})

    # run_id=run.info.run_id
    # model_path = "model"
    # model_uri = "runs:/{}/{}".format(run_id, model_path)
    # mlflow.register_model(model_uri, "lgbm_home_credit_model")
    model_file_name = '{}.pkl'.format(exp_name)
    model_path='./outputs/' + model_file_name
    with open(os.path.join('./outputs/', model_file_name), 'wb') as file:
        pickle.dump(model, file)
    register_aml_model(model_path, exp_name, run.experiment, run.id)
    return model

def connect_feature_repo():
    global fs

    feast_registry_path = os.getenv("REGISTRY_PATH")
    snowflake_acc = os.getenv("SNOWFLAKE_ACC")
    snowflake_user = os.getenv("SNOWFLAKE_USER")
    snowflake_pass = os.getenv("SNOWFLAKE_PASS")
    snowflake_compute_name= os.getenv("snowflake_compute_name")
    snowflake_database_name= os.getenv("snowflake_database_name")
    snowflake_role_name= os.getenv("snowflake_role_name")
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
        online_store=RedisOnlineStoreConfig(connection_string=redis_conn_string),
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

    # Get AML Workspace
    ws = Workspace.get(
        subscription_id=os.getenv('WS_SUBSCRIPTION_ID'),
        resource_group=os.getenv('WS_RESOURCE_GROUP'),
        name=os.getenv('WS_NAME'))

    print("Connected to AML Workspace")

    #Get Keyvault Client
    kv = ws.get_default_keyvault()
    print("Fetched the KeyVault client")

    os.environ['AZURE_CLIENT_ID'] = kv.get_secret("AZURE-CLIENT-ID")
    os.environ['AZURE_TENANT_ID'] = kv.get_secret("AZURE-TENANT-ID")
    os.environ['AZURE_CLIENT_SECRET'] = kv.get_secret("AZURE-CLIENT-SECRET")

    env = Environment.from_conda_specification(
        name="train_env",
        file_path="config/conda_dependencies.yaml")

    #env.docker.base_image = "swsundaramlcr.azurecr.io/fslibbase:latest"
    env.docker.base_dockerfile = "Dockerfile"

    # env.python.user_managed_dependencies = False

    print("Set environment variables")
    # Get and set snowflake access credentials as environment variable
    env.environment_variables = {
        # 'SNOWFLAKE_USER': kv.get_secret("SNOWFLAKE-USER"),
        # 'SNOWFLAKE_PASS': kv.get_secret("SNOWFLAKE-PASS"),
        # 'SNOWFLAKE_ACC': kv.get_secret("SNOWFLAKE-ACC"),
        # 'REGISTRY_PATH': kv.get_secret("FEAST-REG-PATH"),
        # 'snowflake_compute_name': "COMPUTE_WH",
        # 'snowflake_database_name': "HOME_CREDIT_FEATURES",
        # 'snowflake_role_name': "ACCOUNTADMIN",
        # "REDIS_CONN_STRING": "localhost:6379",
        "AZURE_CLIENT_ID": kv.get_secret("AZURE-CLIENT-ID"),
        "AZURE_TENANT_ID": kv.get_secret("AZURE-TENANT-ID"),
        "AZURE_CLIENT_SECRET": kv.get_secret("AZURE-CLIENT-SECRET")
    }

    os.environ['SNOWFLAKE_USER'] = kv.get_secret("SNOWFLAKE-USER")
    os.environ['SNOWFLAKE_PASS'] = kv.get_secret("SNOWFLAKE-PASS")
    os.environ['SNOWFLAKE_ACC'] = kv.get_secret("SNOWFLAKE-ACC")
    os.environ['REGISTRY_PATH'] = kv.get_secret("FEAST-REG-PATH")
    os.environ['snowflake_compute_name'] = "COMPUTE_WH"
    os.environ['snowflake_database_name'] = "HOME_CREDIT_FEATURES"
    os.environ['snowflake_role_name'] = "ACCOUNTADMIN"
    os.environ['REDIS_CONN_STRING'] = "localhost:6379"

    #### Getting training Data
    print("===Get Entities===")
    snow_creds = {"SNOWFLAKE_ACC": kv.get_secret("SNOWFLAKE-ACC"),
                  "SNOWFLAKE_USER": kv.get_secret("SNOWFLAKE-USER"),
                  "SNOWFLAKE_PASS": kv.get_secret("SNOWFLAKE-PASS")
                 }
    sql_query = 'select SK_ID_CURR, TARGET from  "HOME_CREDIT_DATA"."PUBLIC"."APPLICATION_TRAIN"'
    id_train = get_entities_snowflake(snowflake_creds=snow_creds, entity_sql_query=sql_query)
    print(id_train.info())
    datearray = [datetime(2022,2,24)]
    connect_feature_repo()
    train_df = get_features_feast(id_train, datearray, 'risk_model_fs')
    print(train_df.info())
    #### Preprocessing Data
    print("===Data Preprocessing===")
    #### Drop Target Column
    X, y = drop_target(train_df, "SK_ID_CURR", "TARGET")

    #### Train test split
    X_train, X_test, X_valid, y_train, y_test, y_valid = traintest_split(X, y)

    #### Model Training
    print("===Model Training===")
    model = train_model(X_train, X_test, X_valid, y_train, y_test, y_valid)

    print("Model Training Done!")

if __name__ == '__main__':
    main()
