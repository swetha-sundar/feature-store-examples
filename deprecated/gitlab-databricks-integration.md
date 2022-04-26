# Gitlab - Databricks Integration:
## Gitlab integration in Databricks
    1. Launch the databaricks workspace
        1. Open the “Settings” > “User Settings” page then go to the “Git Integration” tab.
        1. On the “Git provider” field choose “GitLab”
            1. This would display additional fields:
                1. “Git provider email” – provide your email address used in the GitLab
                1. “Token” – provide the Gitlab token
                    1. To create the Gitlab token, do these steps
                        1. Open the Gitlab repository in the browser
                        1. Go to “User Settings” > “Access Tokens” page
                        1. Supply the following:
                            1. Token name - name of the token
                            1. Expiration date
                            1. Scopes – allow the following 
                                - api, read_api, read_repository and write_repository
                        1. Click the “Create personal access token”
                        1. Copy the generated token in the “Your new personal access token” field (tip: scroll above)
                    1. Paste the generated token in previous step to “Token” field
        1. Click “Save” on the “Git Integration” tab once all the fields are set.
        1. Click “Repos” main tab on the main databricks page then click “Add Repo”
            1. Select “Clone remote Git repo” , if not yet selected
            1. Supply the following on these fields
                1. “Git repo URL” – complete https clone path format of the repository
                    1. Doing this would automatically fill the dropdown next to this field and the “Repo name” field
            1. Click “Create” once done. If a message pops-up about that the repo doesn’t have a databricks notebook, just ignore it and continue. The default branch might not have any notebooks yet. 
            1. Switch to the desired branch by clicking the branch name (next to the repository name) 
            1. On the pop-up box click the “Pull” button
            1. Once done, just close this box
            1. Navigate to the desired notebook on “Repos” main tab > [YOUR_USER_NAME] > [REPO_NAME]

## GitLab CI/CD variables
These are the variables in the CI/CD settings that is used by the pipeline.

    1. DATABRICKS_ACCESS_TOKEN - this is a masked variable and the value could be obtained by doing the following:
        1. Launch the databricks workspace
        1. Go to "Settings" > "User Settings"
        1. Click the "Generate New Token" button
            1. Supply the "Comment" and "Lifetime (days)" fields
            1. Click "Generate"
            1. Copy the generated token and click "Done"
    1. DATABRICKS_CLUSTER_ID - this value could be obtained by looking cluster url
        1. On the databricks workspace
        1. Go to "Compute" main tab
        1. Select the desired cluster in the "All-purpose cluster" tab by clicking it
        1. Look at the URL in the browser's address bar, the value would be similar to this "https://adb-990229721285774.14.azuredatabricks.net/?o=990229721285774#setting/clusters/0214-073507-rzclp4rx/configuration". The value after "cluster" in the path is the DATABRICKS_CLUSTER_ID which in this example is "0214-073507-rzclp4rx"
    1. DATABRICKS_HOST - this value could be obtained by looking the databricks workspace url
        1. On the databaricks workspace
        1. Look at the URL in the browser's address bar, the value would be similar to this "https://adb-990229721285774.14.azuredatabricks.net/?o=990229721285774#". The "https://adb-990229721285774.14.azuredatabricks.net" part of the of the URL is the DATABRICKS_HOST.


