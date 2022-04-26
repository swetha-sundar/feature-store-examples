# Airflow setup

For this Feature-Store lifecycle MVP, Airflow is configured in a way that the DAG files in the airflow server would be updated through a cronjob. The Airflow instance periodically pulls from the repository (main branch) and updates the DAG files in the server.

1.	Install Airflow from the Marketplace
    1. Open portal and to the Marketplace
    1. Search for “Apache Airflow Mult-Tier packaged by Bitnami”
    1. Click `Create`
        1. Fill-up the necessary fields:
            1. Basic tab:
                1. Location: for the spike “East Asia” is used
                1. Application password: password used to access the site for the default user named “user”
                1. Database password
            1. Environment Configuration tab:
                1. Select the `SSH Public Key` for the `Authentication type`
                1. `Generate new key pair` for `SSH public key source`
                1. Supply the `Key pair name` - this would be the name `pem` name once created.
        1. Click `Review + create`, if validation passes, click `Create` to create the resources
        1. A `Generate new key pair` dialog box would appear, click `Download private key and create resource`.
        
            Note: This airflow template will automatically generate 4 VMs prefixed with the deployment name specified during creation. The VM with "0" suffix will host the Airflow web application (Airflow instance), which contains the Airflow configuration that the user could then change.
1. Connect to the generated airflow VM
    1. Go to Azure portal (https://portal.azure.com) and locate the resource group where the airflow template was installed
    1. Click the VM ending with "0" (zero)
    1. Click `Connect` in the left pane
    1. Follow the instructions on the terminal. Change the path of the `pem` file to point where the `pem` file was downloaded on step 1.3.3.
1. Set-up ssh to access Gitlab repo
    1. ssh into one of the generated VM from the template – the VM ending with “0” (See step 2) if not yet inside
    1. `ssh-keygen -t rsa -b 2048 -C "<SSH_COMMENT>"`
    1. `cat ~/.ssh/id_rsa.pub`
    1. copy and paste the output above to Gitlab
        1. Open the Gitlab server to your “User Settings”, then “SSH Keys”
        1. Add the ssh key on this page.
1. Setup git repo 
    1. ssh into one of the generated VM from the template – the VM ending with “0” (See step 2) if not yet inside
    1. Setup the repo folder
        1. Go to home directory
        1. `mkdir merlion-repo && cd $_`
        1. `git clone git@gitlab.com:merlion-crew/feature-store.git`
            1. The path of the repo should be `/home/bitnami/merlion-repo/feature-store`. This is the path used by the cronjob that would be set-up on the next step.
1. Setup the cronjob. 
    1. ssh into one of the generated VM from the template – the VM ending with “0” (See step 2) if not yet inside
    1. Run this commend: `crontab -e`
    1. Put this on the end
        1. * */5 * * * cd /home/bitnami/merlion-repo/feature-store && sudo apt-get install git -y && git pull && cp -r /home/bitnami/merlion-repo/feature-store/dags /opt/bitnami/airflow/
        1. Note:
            1. This cronjob would run every 5 mins
            1. Everytime it would run
                1. cd into the git repo folder
                1. would install git – without this the cronjob would fail
                1. would `git pull` on the repo folder
                1. would copy the content from the `dags` folder to airflow configured `dags` folder
            1. To troubleshoot the cronjob
                1. `cat /var/mail/bitnami`
                1. if `sudo` error occurs, remove the `&& sudo apt-get install git -y` portion of the cron command
1. Open the airflow web application to verify installation
    1. Go to Azure portal (https://portal.azure.com) and locate the resource group where the airflow template was installed
    1. Locate the generated public ip resource and copy the DNS name
    1. Paste this DNS name on a browser
    1. If the page is inaccessible
        1. Connect to the generated airflow VM
        1. `chmod 777 /opt/bitnami`
        1. `chmod 777 /tmp`
        1. Restart the VM in the Azure portal
    1. Login using the user and password that was set-up on step 1.3.1.1.2 (application user and password)
    1. Go to the DAGs tab, the DAG files from the repo should be displayed in this tab.
        1. If the DAGs do not come up:
            1. wait for 10-12 mins, which is 5 mins for the cronjob to run then 5 minutes for the airflow scheduler to run.
            1. If the DAGs still don't come up, ssh into the VM (ending with “0”) the run `airflow db reset`
