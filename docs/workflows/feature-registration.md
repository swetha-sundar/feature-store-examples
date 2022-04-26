# Registering features to Azure Blob Storage

## Overview
The first workflow while adding new feature(s) or editing existing feature(s) is the **Feature Definition** and **Feature Registration** workflows.

For a given use case that the ML model is being built for, one needs to perform feature engineering - the process of identifying the most important and relevant data and its tranformations that work well for the model and the usecase. Once feature engineering is complete, the feature values are stored in tables (i.e.) offline storage in the context of Feature Stores.

**Feature Definition**:

Feature Definitions contain:

1. Infrastructure Configuration - offline (Snowflake) and online (Redis) storage and registry (Azure Blob) information
2. The metadata - especially the "features", "data type of each feature", "feature views", "feature service" are all defined as python objects

**Feature Registration**:

Feature registation is a process of storing the metadata (feature definitions) in the Registry i.e. Azure Blob Storage, which can then be used to connect to both offline and online storage during Model Training and Inferencing, and also used while syncing the feature values between offline and online storage.

## Pre-requisites

NOTE: For adding role assignments, you need to be a co-administrator or owner on the subscription/resource group.

1. Create User Assigned Managed Identity (user-mi)
2. Assign privileges to the user-mi:
    1. Go to Azure KeyVault -> Add Role Assignment
    2. Select "Reader" and select the created user-mi and click "Review and Assign"
    3. Add another Role Assignment
    4. Select "Key Vault Secrets User" and select the created user-mi and click "Review and Assign"
    5. Add the following role assignments on the respective Azure resources:
        1. Storage Account -> Role: "Storage Blob Data Contributor"
        2. Managed Identity -> Role: "Reader"
3. Add User_MI as CI/CD variables in the Gitlab environment
    1. Gitlab -> Settings -> CI/CD -> Variables -> Add Variable
    2. USER_MSI: Full Azure Resource ID for the user-mi created in step 1
    3. USER_MSI_CLIENT_ID: Copy only the Client_ID from user-mi resource
    4. KEY_VAULT_NAME: Name of the Azure Key Vault to connect

## Running Gitlab pipeline

1. Ensure that the right Snowflake and Redis connections are available in KeyVault
2. Ensure that the Snowflake compute variables are set right in the [variables template file](../pipelines/.variables.yml)
2. Commit your feature definitions file and ensure that you are calling it in the [Feature Registration CD pipeline](../pipelines/.feature-definitions-cd.yml)
3. Pushing code to your branch should auto-trigger the pipeline with the Feature Registration stage.

## Workflow Output

1. Go to Azure Portal
2. Go to Azure Storage Account -> Blob Containers
3. Choose the right folder path as specified in the Feast Registry and you should see a registry db file in the container with all the feature metadata.