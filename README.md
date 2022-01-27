# Feature Store for ML

## Overview

Feature Store example using Feast library, Snowflake as Offline Store and Redis  as  Online Store

## Prerequisites

1. Ensure you have a Snowflake Account with the following setup:
    - a compute instance/warehouse
    - a database created for your data source
    - a role created with read/write privileges on the database

2. Ensure your Redis local server/instance is up and running
3. Update the `feature_store.yaml` file with your Snowflake account details and database name

## Usage Instructions for Feast

NOTE: The example provided here works for `0.17` version of feast.

1. Create a python virtual environment to install all libraries
    `virtualenv <env_name>`
2. Activate the virtual environment
    `source <env_name>/bin/activate`
3. Install all dependencies required for the example
    `pip install -r requirements.txt`
4. Run the following commands from `feature_repo` directory
5. To upload feature values(data) into your database, run `python upload_data.py`
6. To create the **feature registry** and register the features, run `python create_features.py`
7. To consume/fetch the features from offline store(Snowflake), run `python consume_features.py`
8. To fetch feature from online store(Redis), run `python get_online_features.py`
