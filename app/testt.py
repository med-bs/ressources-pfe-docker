#import os
#os.environ["PYSPARK_SUBMIT_ARGS"] = "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2" 
from pyspark.sql import SparkSession
# create a Spark session
spark = SparkSession.builder.appName("Kafkaconsumer").getOrCreate()

print('\n\n test \n\n')

import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2 pyspark-shell'

# create a Kafka stream
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "c9900bf7da2f:9092") \
    .option("subscribe", "dbserver2.inventory.addresses") \
    .option("startingOffsets", "latest") \
    .load()

# select the value column from the Kafka stream
value_df = df.selectExpr("CAST(value AS STRING)")

# print the value column to the console
query = value_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# wait for the query to terminate
query.awaitTermination()