# Gitlab runner configuration and installation set-up

This documents on how to create a Gitlab runner hosted on AzureVM that would be linked to the Gitlab server.

## Steps
1. Create an Azure VM
    
    Current VM configuration:
        
        - Size: Standard B2s (2vcpus, 4Gib memory)
        - Resource group: rg-merlion-feature-store-project
        - Location: Southeast Asia
1. VM Setup
    1. ssh into the VM
    1. Install docker - based on [this](https://docs.docker.com/install/linux/docker-ce/ubuntu])
        1. `sudo apt-get update`
        1. `sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common`
        1. `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -`
        1.  `sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"`
        1. `sudo apt-get update`
        1. `sudo apt-get install docker-ce`
    1. Install and run gitlab-runner docker container
        1. `sudo docker run -d --name gitlab-runner --restart always  -v /srv/gitlab-runner/config:/etc/gitlab-runner -v /var/run/docker.sock:/var/run/docker.sock gitlab/gitlab-runner:latest`
    1. Register gitlab-runner with gitlab
        1. `sudo docker exec -it gitlab-runner gitlab-runner register`
            
            Note: Enter the necessary token and gitlab url when prompted. See the settings in the Gitlab server project's CI/CD settings in the `Runners` section.

