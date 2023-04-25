# pip install pyspark
# pip install elasticsearch

import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2,org.elasticsearch:elasticsearch-spark-30_2.12:7.16.2,com.fasterxml.jackson.module:jackson-module-scala_2.12:2.13.0 pyspark-shell'

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

from pyspark.sql import SparkSession

# Create a SparkSession object
spark = SparkSession.builder.appName("ElasticsearchWriter").getOrCreate()

# create a Kafka stream
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver2.inventory.addresses") \
    .load()

# select the value column from the Kafka stream
value_df = df.selectExpr("CAST(value AS STRING)")

# Create an Elasticsearch client
es = Elasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])

# Define the Elasticsearch index name //---and document type
es_index = "my_index"

# Create a mapping for the Elasticsearch index
# Define the index mapping
mapping = {
    "mappings": {
        "properties": {
            "value": {"type": "text"}
        }
    }
}

# Check if the index exists, and create it if it does not
# Create the Elasticsearch index if it doesn't exist
if not es.indices.exists(index=es_index):
    try:
        es.indices.create(index=es_index, body=mapping)
    except RequestError as e:
        print(f"Index creation failed: {e}")
        exit(1)
    print(f"Created Elasticsearch index '{es_index}'")

# Write the streaming DataFrame to Elasticsearch
def write_to_es(df, epoch_id):
    df.write.format("org.elasticsearch.spark.sql") \
        .option("es.nodes", "elasticsearch") \
        .option("es.port", "9200") \
        .option("es.resource", es_index) \
        .save()

# select the value column from the Kafka stream
value_df = df.selectExpr("CAST(value AS STRING)")


# Call the write_to_es function on each micro-batch of data
query = value_df.writeStream.foreachBatch(write_to_es).start()

# Start the query to write to console
query = value_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# Wait for the stream to finish
query.awaitTermination()