# Choosing a Training Compute Option

When using Azure Machine Learning or other online tools for training Machine Learning models, there are many different options for how to host that compute. This document will focus on examining using Azure Kubernetes Service (AKS), as well as the Azure Machine Learning Compute Clusters for scheduling training jobs and pipelines. This is not a comprehensive exploration of all compute options, but should provide useful context for the various types of compute that are available to data scientists and engineers when using Azure.

The companion to this document is found in [notebooks/aks-aml-training.ipynb](../notebooks/aks-aml-training.ipynb).

- [Choosing a Training Compute Option](#choosing-a-training-compute-option)
  - [Azure Kubernetes Service (AKS)](#azure-kubernetes-service-aks)
    - [Setup](#setup)
    - [Training a Model](#training-a-model)
    - [Considerations](#considerations)
  - [Azure ML Compute Cluster](#azure-ml-compute-cluster)
    - [Setup](#setup-1)
    - [Training a Model](#training-a-model-1)
    - [Considerations](#considerations-1)
  - [Comparison](#comparison)

## Azure Kubernetes Service (AKS)

AKS is a managed Kubernetes service hosted on Azure which provides simplifed deployment and management of a Kubernetes cluster, while still providing flexibility on networking, monitoring, and other features that a customer way wish to add or change to their cluster. Azure will handle health monitoring and maintenance with the managed master node, while the end user configures the agent clusters and nodes.

When using AKS as a standalone service, it works just as any Kubernetes cluster should be expected to - users can manage which Docker containers are deployed to which nodes, how traffic is load balanced, etc. When using AKS in conjunction with Azure ML, there are some limitations, which are outlined in the [official documentation](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-kubernetes?tabs=python#limitations).

### Setup

Within the Azure ML Documentation, it describes the process of provisioning an AKS cluster using the Azure ML Python SDK. Based on our current testing, this creates an [Inference Cluster](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-kubernetes?tabs=python) which does not allow end users to install the necessary extensions to use AKS for training. This may be something that can be resolved, however at this time there is no documented path to do so using the Azure ML SDK.

It is important to note that the ability to use a Kubernetes cluster for model training is currently in a Preview within Azure ML, and is not fully supported. This document outlines the necessary steps to perform this task, but provides no guarantees that these steps will always work in the future, as preview offerings often change.

First and foremost, to use a Kubernetes cluster for training, you must provision a Kubernetes cluster. To do so in Azure, you have the standard options of the [Azure CLI](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough), [Azure Portal](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough-portal), or [ARM Templates](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough-rm-template).

Before attaching an existing AKS cluster, the [Azure Machine Learning extension](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-attach-arc-kubernetes?tabs=studio#deploy-azure-machine-learning-extension) must be installed on the Kubernetes cluster. This requires the following Azure CLI commands to be executed (further detail on these commands is available in the link above):

```bash
# These register the necessary providers in Azure for configuring Kubernetes. They may take approx. 10 minutes to finish
az provider register --namespace Microsoft.KubernetesConfiguration
az provider register --namespace Microsoft.ContainerService

# Next, add the AKS-ExtensionManager feature
az feature register --namespace "Microsoft.ContainerService" --name "AKS-ExtensionManager"

# Add the k8s-extension manager to your Azure CLI
az extension add --name k8s-extension

# Finally, add the Azure ML Extension to your AKS cluster
az k8s-extension create --name arcml-extension --extension-type Microsoft.AzureML.Kubernetes --config enableTraining=True --cluster-type managedClusters --cluster-name <CLUSTER NAME> --resource-group <RESOURCE GROUP> --scope cluster --auto-upgrade-minor-version False
```

Once the Azure ML Extension has been installed into the cluster, the cluster may then be attached to the Azure ML Workspace. To do this, you must use the preview `azureml.core.compute.KubernetesCompute` module from the Azure ML Python SDK. An example is shown below:

```python
from azureml.core.compute import KubernetesCompute, ComputeTarget
resource_id = "/subscriptions/12f4bdb4-aa23-4f3d-bff0-7eec97b0443f/resourceGroups/rg-merlion-feature-store-project/providers/Microsoft.ContainerService/managedClusters/merlionaks"
cluster_name = 'merlionaks'
# Verify that cluster does not exist already
try:
    aks_target = ComputeTarget(workspace=ws, name=cluster_name)
    print('Found existing cluster, use it.')
except ComputeTargetException:
    # To use a different region for the compute, add a location='<region>' parameter
    # resource ID for the Kubernetes cluster and user-managed identity
    attach_config = KubernetesCompute.attach_configuration(
        resource_id=resource_id,
        namespace="default",
        )
    aks_target = ComputeTarget.attach(ws, cluster_name, attach_config)


aks_target.wait_for_completion(show_output=True)
```
### Training a Model

To train a model using this Kubernetes cluster, it is simply a matter of specifying it as a "ComputeTarget" for a training job. There are multiple ways to create a training job, but the simplest example is a `ScriptRun`, as shown below:

```python
from azureml.core import Experiment
from azureml.core import Workspace, Environment

ws = Workspace.from_config()
# Specify the name of the experiment in the Workspace to run this under
experiment_name = 'aks_vs_amlcompute'
experiment = Experiment(workspace=ws, name=experiment_name)

# We will use a curated environment, which is a Microsoft managed Docker image
myenv = Environment.get(workspace=ws, name="AzureML-Tutorial")

# Specify a ScriptRunConfig to use the AKS target as the compute
aks_src = ScriptRunConfig(source_directory='./notebook-scripts',
                      script='train.py',
                      compute_target=aks_target,
                      environment=myenv)

aks_src.run_config.environment = myenv

# Create the training run
run = experiment.submit(aks_src)
```
### Considerations

Most critically, it is important to know that the capability of targeting a Kubernetes cluster for training is in preview. While tests so far have shown it to be stable, this feature does not have an SLA.

Additionally, when comparing different training compute options, the most significant downside of using a Kubernetes cluster is the additional overhead of managing the cluster. While Azure ML will deploy the training jobs as necessary, it is not able to auto-scale the Kubernetes nodes, which may lead to additional costs or slow runs (in the case of too many/few nodes available at a given time).

There may be additional hurdles when using Kubernetes as a compute target when attempting to use a cluster which has strict networking requirements. Please see [these documents](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-attach-arc-kubernetes?tabs=studio#prerequisites) for additional networking prerequisites.

## Azure ML Compute Cluster

Azure Machine Learning Compute Clusters are fully managed single or multi-node compute infrastructure which are capable of performing training or batch inference operations. Compute Clusters are capable of auto-scaling down to 0 nodes (incurring no cost when not active), and scaping up when a job is submitted.

Jobs run on Compute Clusters are containerized, and may be run inside of virtual networks for additional security.

### Setup

The simplest way to provision a Compute Cluster is from the Azure ML Studio - simply click on "Compute" -> "Compute Clusters" -> "+ New", and specify the size and number of VM nodes required.

Additionally, you can use the Azure ML Python SDK to programatically provision Compute Clusters:

```python
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException

# Choose a name for your CPU cluster
cpu_cluster_name = "merlion-cpu"

# Verify that cluster does not exist already
try:
    cpu_cluster = ComputeTarget(workspace=ws, name=cpu_cluster_name)
    print('Found existing cluster, use it.')
except ComputeTargetException:
    # To use a different region for the compute, add a location='<region>' parameter
    compute_config = AmlCompute.provisioning_configuration(vm_size='STANDARD_DS3_V2',
                                                           max_nodes=4)
    cpu_cluster = ComputeTarget.create(ws, cpu_cluster_name, compute_config)

cpu_cluster.wait_for_completion(show_output=True)
```
Additional details on full customizable options for Compute Clusters are in the [official docs](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-compute-cluster?tabs=python)

### Training a Model

Training a model is identical to using the AKS cluster seen above, simply specify the Compute Cluster as the `ComputeTarget`

```python
from azureml.core import Experiment
from azureml.core import Workspace, Environment

ws = Workspace.from_config()
# Specify the name of the experiment in the Workspace to run this under
experiment_name = 'aks_vs_amlcompute'
experiment = Experiment(workspace=ws, name=experiment_name)

# We will use a curated environment, which is a Microsoft managed Docker image
myenv = Environment.get(workspace=ws, name="AzureML-Tutorial")

# Specify a ScriptRunConfig to use the AKS target as the compute
cpu_src = ScriptRunConfig(source_directory='./notebook-scripts',
                      script='train.py',
                      compute_target=cpu_target,
                      environment=myenv)

cpu_src.run_config.environment = myenv

# Create the training run
run = experiment.submit(cpu_src)
```
### Considerations

Compute Clusters are only availble to jobs executed from Azure ML - the VM instances are not visible as separate resources within a Resource Group, and are not accessable directly for workloads.

If system-level configurations are requried to run a job (to be configured outside of the container), then Compute Clusters are likely not the correct choice.
## Comparison

To simplify a larger point, there is always a trade-off between ease-of-use and flexibility, which is the biggest comparison for attaching a Kubernetes instances or using a Compute Cluster.

Pros of AKS:
- More control of underlying infrastructure
- Direct control of number of active nodes
- Multi-purpose single resource

Pros of Compute Cluster
- Single function, nearly 0-touch
- Auto-scaling
- Fully managed

