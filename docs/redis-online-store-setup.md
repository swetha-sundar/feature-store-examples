# Feast Online Store with Azure Cache for Redis 
## Overview
This section includes two settings: 
 - setting up Azure Redis Cache as an online feature store and
 - setting up connectivity between Azure Databricks and Azure Redis Cache with Redis access keys stored in Azure Key Vault.

## Set up Azure Cache for Redis
1. Navigate to Azure Portal (https://portal.azure.com)
1. Create a resource(https://portal.azure.com/#create/hub) and select Azure Cache for Redis.
1. Create a new resource group or select from an existing resource group.
1. Enter a DNS name eg. grabtaxifsredis
1. Select a location eg. SouthEastAsia
1. Choose a plan. For testing and development, select Basic C0 or Standard C1
1. For development and testing, select public network on the next tab. You may choose private network or a connection over existing vnet. 
1. Enable non TLS port, select Redis version 6.
1. Finally review and create.

## Set up Azure Databricks to use Azure Cache for Redis
1. Go to your Azure Databricks. For example: https://adb-990229721285774.14.azuredatabricks.net/?o=990229721285774
1. Click Compute on the left hand pane.
1. Go to Cluster
1. Go to Libraries
1. Click Install new
1. Select Library source Maven
1. Choose Search package
1. Drop down and select Maven central repository
1. Search for spark-redis
1. Install spark-redis_2.12 version 3.0

## Testing Azure Cache for Redis with Databricks connection
1. Navigate to your Azure Databricks workspace.
1. Click your username and from the drop down menu, select import notebook.
1. Import redis-databricks-connector.html (This is an example notebook that connects to Redis via secret retrived from Azure key vault).
1. Make sure a cluster is attached before running the notebook, you should see a green dot on top left corner.
1. Run the cells in the notebook.

### What does the notebook do?
1. Import Redis library
1. Retrieve a key from Azure Key Vault. You can provide your own by changing the scope and key field.
1. Test connection to the Redis Cache by writing a list of items('Merlion', 'Is', 'Awesome') and retrieving it back. 
``` 
// Create and Write list to Redis
val stringListRDD = sc.parallelize(Seq("Merlion", "is", "awesome"))
sc.toRedisLIST(stringListRDD, "listkey1")(redisConfig)
```
```
// Reading List from Redis
val keysRDD = sc.fromRedisKeyPattern("listkey*")(redisConfig)
val listRDD = keysRDD.getList

// Print out list
listRDD.collect()
```


More on list: https://redis.io/topics/data-types-intro#redis-lists
