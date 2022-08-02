from azureml.core import Experiment
from azureml.core import Workspace, Environment, ScriptRunConfig
import os

ws = Workspace.get(
        subscription_id=os.getenv('WS_SUBSCRIPTION_ID'),
        resource_group=os.getenv('WS_RESOURCE_GROUP'),
        name=os.getenv('WS_NAME'))
compute_name = os.getenv("AML_COMPUTE_NAME")


if compute_name in ws.compute_targets:
    aks_target = ws.compute_targets[compute_name]
else:
    print("Compute " + compute_name + " does not exist in the AML Workspace.")
    exit(1)

experiment_name = os.getenv("AML_EXPERIMENT_NAME")
experiment = Experiment(workspace=ws, name=experiment_name)

kv = ws.get_default_keyvault()

# We will use a curated environment, which is a Microsoft managed Docker image
env = Environment.from_conda_specification(name="train_env",
                                             file_path="./config/conda_dependencies.yaml")
env.docker.base_image = None
env.docker.base_dockerfile = "./Dockerfile"

env.python.user_managed_dependencies = False

# Specify a ScriptRunConfig to use the AKS target as the compute
aks_src = ScriptRunConfig(source_directory='./risk_model',
                      script='train.py',
                      compute_target=aks_target,
                      environment=env)

aks_src.run_config.environment = env

aks_src.run_config.environment_variables = {
        'SNOWFLAKE_ACC': kv.get_secret("SNOWFLAKE-ACC"),
        'SNOWFLAKE_USER': kv.get_secret("SNOWFLAKE-USER"),
        'SNOWFLAKE_PASS': kv.get_secret("SNOWFLAKE-PASS"),
        'REGISTRY_PATH': kv.get_secret('FEAST-REGISTRY-PATH'),
        'snowflake_compute_name': kv.get_secret("SNOWFLAKE-COMPUTE"),
        'snowflake_database_name': kv.get_secret("SNOWFLAKE-DB"),
        'snowflake_role_name': kv.get_secret("SNOWFLAKE-ROLE"),
        "REDIS_CONN_STRING": kv.get_secret("REDIS-CONN-STRING"),
        "AZURE_CLIENT_ID": kv.get_secret("AZURE-CLIENT-ID"),
        "AZURE_TENANT_ID": kv.get_secret("AZURE-TENANT-ID"),
        "AZURE_CLIENT_SECRET": kv.get_secret("AZURE-CLIENT-SECRET")
}

# Create the training run
run = experiment.submit(aks_src)
