# Setup Airflow on Azure Kubernetes Service (AKS)

0. Make sure the following command line utilities are installed:
`az` (Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-macos)
`kubectl` (https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/)
`helm` (https://helm.sh/docs/intro/install/)

1. Login to azure account using azure cli, and authenticate:
`az login`

2. Assuming there is an existing resource group already (if not create a resource group as shown below), create an AKS cluster with 3 nodes as below:
CLUSTER_NAME = "airflow-aks"
RESOURCE_GROUP = "gxs-msft-rg1"

Create Resource Group (if not existing already): `az group create --name $RESOURCE_GROUP --location eastasia`

Create AKS: `az aks create --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME --kubernetes-version 1.23.3 --node-count 3 --location eastasia --generate-ssh-keys`

3. Check connection with the created AKS cluster by running the following command:
`az aks get-credentials -g $RESOURCE_GROUP -n $CLUSTER_NAME`

4. Create an Azure Container Registry (ACR):
ACR_NAME = "gxsmsftacr"

`az login`
`az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic`

5. Create a namespace for Airflow installation:
a. Create a namespace for airflow: `kubectl create namespace airflow`
b. List namespaces to confirm: `kubectl get namespaces`
c. Run this command one more time: `az aks get-credentials -g $RESOURCE_GROUP -n $CLUSTER_NAME`

6. Helm install Airflow
`helm repo add apache-airflow https://airflow.apache.org`
`helm repo update`
`helm search repo airflow`
`helm install airflow apache-airflow/airflow --namespace airflow --debug`

In the order of the commands above, you add the official repository of the Apache Airflow Helm chart. Then you update the repo to make you got the latest version of it. You can take a look at the current version with search repo. Finally, deploy Airflow on Kubernetes with Helm install. The application will get the name airflow and the flag –debug allows to check if anything goes wrong during the deployment.

After a few minutes, you should be able to see your Pods running, corresponding to the different Airflow components.

`kubectl get pods -n airflow`
`helm ls -n airflow`
Basically, each time a new version of Airflow chart is deployed (after a modification or an update), you will obtain a new release. One of the most important field to take a look at is REVISION. This number will increase, if you made a mistake you can rollback to a previous revision with helm rollback.

At this point you have successfully deployed Airflow on Kubernetes.

To access the Airflow UI, execute the following command:
`kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow`

Then go to "localhost:8080" to access the Airflow Webserver UI.

7. Configure Airflow setup
There are two steps to this, before performing a `helm upgrade ...`
a. To update the Airflow values.yaml file with all the appropriate config settings such as:
- webserver-secret-key, 
- executor type,
- environment variables config file,
- gitSync etc.
b. Install dependencies with Airflow on Kubernetes: to update the official Airflow Helm chart with any additional dependencies and providers that you may need.

In our case, we may need to include a few additional providers on top of the official Airflow Helm Chart

Note: Refer to airflow-setup directory for all the required files in the following steps:

Step a:
`helm show values apache-airflow/airflow > values.yaml`
Once it’s loaded, modify your Airflow instance. First, modify the Airflow version. Instead 2.2.3, change it to 2.2.4 (this is the latest version at the time of documentation):
defaultAirflowTag: "2.2.4"
airflowVersion: "2.2.4"

In addition, you can specify the executor to KubernetesExecutor as the executor by default is the CeleryExecutor.
executor: "KubernetesExecutor"

Also, if you have some variables or connections that you want to export each time your Airflow instance gets deployed, you can define a ConfigMap. Open variables.yaml. This ConfigMap will export the environment variables under data. Great to have some bootstrap connections/variables.

To add it to your Airflow deployments, in values.yaml modify extraEnvFrom:
extraEnvFrom: |
configMapRef:
name: 'airflow-variables' 

Then add the ConfigMap to the cluster:
`kubectl apply -f variables.yaml`

And finally, deploy Airflow on Kubernetes again.
`helm ls -n airflow`
`helm upgrade --install airflow apache-airflow/airflow -n airflow -f values.yaml --debug`
`helm ls -n airflow`
This time, you pass the file values.yaml to the command helm upgrade and check the Airflow release before and after the upgrade so that you make sure it gets correctly deployed.


Step b: Install dependencies with Airflow on Kubernetes
Create a file "requirements.txt", and find the details of all the required providers (this can be found in the Astronomer Registry: https://registry.astronomer.io/) and their latest versions as shown in the file.
 and add them to the "requirements.txt" file.

Then, create a Dockerfile, with the latest Airflow version (2.2.4 at the time of writing this doc), and including the requirements as shown in the example Dockerfile.

Then build the custom docker image:
`docker build -t airflow-custom:1.0.0 .`

Tag the docker image to ACR container registry:
`docker tag airflow-custom:1.0.0 $ACR_NAME.azurecr.io/airflow-custom:1.0.0`

Push the tagged image to ACR:
`docker push $ACR_NAME.azurecr.io/airflow-custom:1.0.0`

Now, modify the values.yaml file for the following two values to use the custom docker image in ACR:
defaultAirflowRepository: gxsmsftacr.azurecr.io/airflow-custom
defaultAirflowTag: "1.0.0"

Run: `python3 -c 'import secrets; print(secrets.token_hex(16))'`
And add the generated <secret_key> to the following variable in values.yaml:
webserverSecretKey: <secret_key>

And now upgrade the chart:
`helm upgrade --install airflow apache-airflow/airflow -n airflow -f values.yaml --debug`
`helm ls -n airflow`

If the Airflow webserver UI (localhost:8080) is disconnected because of upgrade, please run the following command again:
`kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow`

You can check the list of providers to confirm if the newly added providers are included like so:
`kubectl exec <webserver_pod_id> -n airflow -- airflow providers list`

8. Deploy DAGs to Airflow on AKS using GitSync

There are different ways of deploying your DAGs in an Airflow instance running on Kubernetes but we will be using the GitSync approach here. GitSync acts as a side car container that will run along with your PODs to synchronise the 'dags/' folder (in the PODs) with the Git repository where your DAGs are stored.

To deploy the DAGs within your Kubernetes cluster, we will need to update a few things in values.yaml (from lines 1464 to 1506):

a. Go to your private repository and create an SSH key (if you don’t have one)
b. Go to the settings of the repository. Then deploy your public key in the “Deploy keys” section (don’t select “Allow write access”). 
c. In the 'values.yaml' you need to configure your chart with `gitSync`. Enable it by typing `true`.
d. Assuming the DAGs are 'dags/' folder, and the gitlab repo URL is 'git@gitlab.com:merlion-crew/feature-store.git', copy the SSH link and edit the repo link like so: add "ssh://" as a prefix and change ":" to "/", so:
'git@gitlab.com:merlion-crew/feature-store.git' becomes --> 'ssh://git@gitlab.com/merlion-crew/feature-store.git'
e. As you need to give your private key you want to use a Secret for additional security:

Type `kubectl create secret generic airflow-ssh-git-secret --from-file=gitSshKey=` and point to where your private key is.
In our example it looks like this: 
`kubectl create secret generic airflow-ssh-git-secret --from-file=gitSshKey=/Users/deepak.jayakumaran/.ssh/gl_merlion_crew_deploy_keys -n airflow`


```
  gitSync:
    enabled: true

    # git repo clone url
    # ssh examples ssh://git@github.com/apache/airflow.git
    # git@github.com:apache/airflow.git
    # https example: https://github.com/apache/airflow.git
    repo: ssh://git@gitlab.com/merlion-crew/feature-store.git
    branch: 304_testing_airflow_setup
    rev: HEAD
    depth: 1
    # the number of consecutive failures allowed before aborting
    maxFailures: 0
    # subpath within the repo where dags are located
    # should be "" if dags are at repo root
    subPath: "dags"
    # if your repo needs a user name password
    # you can load them to a k8s secret like the one below
    #   ---
    #   apiVersion: v1
    #   kind: Secret
    #   metadata:
    #     name: git-credentials
    #   data:
    #     GIT_SYNC_USERNAME: <base64_encoded_git_username>
    #     GIT_SYNC_PASSWORD: <base64_encoded_git_password>
    # and specify the name of the secret below
    #
    # credentialsSecret: git-credentials
    #
    #
    # If you are using an ssh clone url, you can load
    # the ssh private key to a k8s secret like the one below
    #   ---
    #   apiVersion: v1
    #   kind: Secret
    #   metadata:
    #     name: airflow-ssh-secret
    #   data:
    #     # key needs to be gitSshKey
    #     gitSshKey: <base64_encoded_data>
    # and specify the name of the secret below
    sshKeySecret: airflow-ssh-git-secret
```

f. Check if it’s been deployed successfully. Go back to the Airflow UI and refresh. Your DAGs should appear there in 5 minutes. Once they are loaded any future modifications will be uploaded every 60 seconds.