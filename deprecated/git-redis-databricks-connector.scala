// Databricks notebook source
// MAGIC %md
// MAGIC # **Connecting to Redis Database**
// MAGIC In this example, we'll query Redis using its Spark Package Driver.
// MAGIC 
// MAGIC This notebook covers the following:
// MAGIC * Part 1: Set up your Redis Connection
// MAGIC * Part 2: Read & Write Strings to/from Redis
// MAGIC * Part 3: Read & Write Hashes to/from Redis
// MAGIC * Part 4: Read & Write Lists to/from Redis
// MAGIC * Part 5: Read & Write Sets to/from Redis

// COMMAND ----------

// MAGIC %md # Test for parameter passing

// COMMAND ----------


dbutils.widgets.text("PipelineParam", "default value", "Pipeline passed value")
var pipeValue = dbutils.widgets.get("PipelineParam")

println(pipeValue)

// COMMAND ----------

// MAGIC %md ##Setup Redis Connection
// MAGIC ###Load the Redis Spark Package and attach Library to clusters
// MAGIC * Redis has a [Spark Package](http://spark-packages.org/package/RedisLabs/spark-redis) that you can download and attach to your cluster

// COMMAND ----------

import com.redislabs.provider.redis._

// COMMAND ----------

// MAGIC %md ###Set Redis Connection Properties & read from keyvault

// COMMAND ----------

val redisServerDnsAddress = "redis-fs.redis.cache.windows.net"
val redisPortNumber = 6379
val redisPassword = dbutils.secrets.get(scope = "merlion", key = "REDIS-ACCESS-KEY")
val redisConfig = new RedisConfig(new RedisEndpoint(redisServerDnsAddress, redisPortNumber, redisPassword))

// COMMAND ----------

// MAGIC %md ##Test Connection: Read & Write Lists to/from Redis

// COMMAND ----------

// Create and Write list to Redis
val stringListRDD = sc.parallelize(Seq("Merlion", "is", "awesome"))

sc.toRedisLIST(stringListRDD, "listkey1")(redisConfig)

// COMMAND ----------

// Reading List from Redis
val keysRDD = sc.fromRedisKeyPattern("listkey*")(redisConfig)

val listRDD = keysRDD.getList

// COMMAND ----------

// Print out list
listRDD.collect()

// COMMAND ----------


