# pip install pyspark
# pip install redis


import os
import redis
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2 pyspark-shell'

from pyspark.sql import SparkSession

# create a Spark session
spark = SparkSession.builder.appName("kafkaConsumer").getOrCreate()

# create a Kafka stream
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver2.inventory.addresses") \
    .load()

# select the value column from the Kafka stream
value_df = df.selectExpr("CAST(value AS STRING)")

# define a function to save the value in Redis
def save_to_redis(rdd):
    redis_host = "redis"
    redis_port = 6379
    redis_db = 0
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    for record in rdd.collect():
        key = redis_client.incr("mykey")
        redis_client.set(key, record[0])
        value = redis_client.get(key)
        print("*****")
        print(value)
        print("****")

# save the value in Redis
value_df \
    .writeStream \
    .foreachBatch(save_to_redis) \
    .start()

print("********------------************")

# start the query to print the value to the console
query = value_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# wait for the query to terminate
query.awaitTermination()
