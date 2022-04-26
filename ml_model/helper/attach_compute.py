
import traceback
from azureml.core import Workspace
from azureml.core.compute import ComputeTarget
from azureml.exceptions import ComputeTargetException
from azureml.core.compute import KubernetesCompute

def get_compute(workspace: Workspace, compute_name: str, cluster_name: str, resource_id: str):  # NOQA E501
    try:
        if compute_name in workspace.compute_targets:
            compute_target = workspace.compute_targets[compute_name]
            if compute_target and type(compute_target) is KubernetesCompute:
                print("Found existing compute target " + compute_name + " so using it.") # NOQA
        else:
            attach_config = KubernetesCompute.attach_configuration(
                resource_id=resource_id,
                namespace="default",
            )
            compute_target = ComputeTarget.attach(workspace, cluster_name, attach_config)
            compute_target.wait_for_completion(show_output=True)
        return compute_target
    except ComputeTargetException:
        traceback.print_exc()
        print("An error occurred trying to provision compute.")
        exit(1)

aml_workspace = Workspace.get(
        name="mlops-AML-WS",
        subscription_id="371e8e7f-bce0-4db0-9df5-d88805b41101",
        resource_group="mlops-RG"
    )
get_compute(aml_workspace, "aks-train", "/subscriptions/371e8e7f-bce0-4db0-9df5-d88805b41101/resourcegroups/mlops-RG/providers/Microsoft.ContainerService/managedClusters/aks")



a