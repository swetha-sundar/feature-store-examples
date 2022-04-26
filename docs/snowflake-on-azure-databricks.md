# Access Snowflake from Azure Databricks

There are 3 main steps to access Snowflake from a Databricks notebook. 

1. Link an Azure Key Vault to Databricks Cluster
2. Add Snowflake Credentials to Key Vault
3. Fetch the Snowflake Credentials from Key Vault


Once the key vault is set up to be accessed from your Azure Databricks cluster, you can add your snowflake credentials as secrets to your key vault and pull them as done below:

```
user = dbutils.secrets.get("data-warehouse", "SNOWFLAKE_USER")
password = dbutils.secrets.get("data-warehouse", "SNOWFLAKE_PASS")
```

Note that you will substitute the name of your secret in lines 8 and 9 to pull the credentials. E.g., if you named your SNOWFLAKE_USER key as SF_USERNAME, then you'd use SF_USERNAME as a key instead. We can then connect to the snowflake instance using these specific options. Note that Snowflake schemas, warehouses and databases are all case-sensitive information and are converted to uppercase by Snowflake upon entry.

```
snowflake connection options
options = {
  "sfUrl": "<snowflake-url>",
  "sfUser": user,
  "sfPassword": password,
  "sfDatabase": "<snowflake-database>",
  "sfSchema": "<snowflake-schema>",
  "sfWarehouse": "<snowflake-cluster>"
}
```

Command to write:

```
spark.range(5).write \
  .format("snowflake") \
  .options(**options) \
  .option("dbtable", "<snowflake-database>") \
  .save()
```

Command to read back the written data:

```
df = spark.read \
  .format("snowflake") \
  .options(**options) \
  .option("query",  "select 1 as my_num union all select 2 as my_num") \
  .load()

df.show()
```

