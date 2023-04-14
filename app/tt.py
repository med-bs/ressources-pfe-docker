# pip install pyspark
# pip install redis


import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2 pyspark-shell'

import redis
import json

from pyspark.sql import SparkSession

# create a Spark session
spark = SparkSession.builder.appName("kafkaConsumer").getOrCreate()

# Create a Redis client
# Connect to Redis
redis_host = 'redis'
redis_port = 6379
redis_db = 0
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

# Define a function to save data to Redis
def save_to_redis(df, epoch_id):
    
    # Convert the DataFrame to a list of dictionaries
    data = df.toJSON().map(json.loads).collect()
    
    # Save each record to Redis
    for record in data:
        key = redis_client.incr("mykey") # Auto key
        redis_client.set(key, json.dumps(record)) #save


# create a Kafka stream
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver2.inventory.addresses") \
    .load()

# select the value column from the Kafka stream
value_df = df.selectExpr("CAST(value AS STRING)")

# save the value in Redis
value_df \
    .writeStream \
    .foreachBatch(save_to_redis) \
    .start()

# Start the query to write to console
query = value_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# wait for the query to terminate
query.awaitTermination()
