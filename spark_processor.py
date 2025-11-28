from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, count, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import os
import sys

# Configuración desde variables de entorno
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# 1. Configuración de la Sesión Spark CON KAFKA
spark = SparkSession.builder \
    .appName("UpTimerStreamProcessor") \
    .config("spark.master", "local[*]") \
    .config("spark.sql.shuffle.partitions", 3) \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

# Ajustar nivel de logs para evitar ruido en consola
spark.sparkContext.setLogLevel("WARN")

# 2. Definición del Schema (Debe coincidir con tu producer)
json_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("url", StringType(), True),
    StructField("status_code", IntegerType(), True),
    StructField("latency_ms", DoubleType(), True),
    StructField("db_status", StringType(), True)
])

# 3. Lectura desde Kafka (Ingesta)
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", "eventos_raw") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# 4. Parseo y Limpieza
# Convertimos el value (bytes) a String y luego a JSON con el schema
df_parsed = df_kafka.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), json_schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType())) # Convertir string ISO a Timestamp real

# --- PROCESO A: GUARDAR RAW DATA (LAKE 1) ---
# Checkpoint necesario para tolerancia a fallos
query_raw = df_parsed.writeStream \
    .format("parquet") \
    .option("path", "./datalake/lake1_raw") \
    .option("checkpointLocation", "./datalake/checkpoints/raw") \
    .outputMode("append") \
    .start()

# --- PROCESO B: AGREGACIÓN (LAKE 2) ---
# Calculamos métricas cada 1 minuto (Ventana de tiempo)
df_metrics = df_parsed \
    .withWatermark("timestamp", "1 minute") \
    .groupBy(
        window(col("timestamp"), "1 minute"),
        col("url")
    ) \
    .agg(
        avg("latency_ms").alias("avg_latency"),
        count("*").alias("total_pings"),
        # Contamos cuántos no fueron 200 OK
        count(when(col("status_code") != 200, 1)).alias("error_count")
    ) \
    .select(
        col("window.start").alias("start_time"),
        col("window.end").alias("end_time"),
        col("url"),
        col("avg_latency"),
        col("total_pings"),
        col("error_count")
    )

query_agg = df_metrics.writeStream \
    .format("parquet") \
    .option("path", "./datalake/lake2_metrics") \
    .option("checkpointLocation", "./datalake/checkpoints/metrics") \
    .outputMode("append") \
    .start()

print("Streaming iniciado... Presiona Ctrl+C para detener.")
spark.streams.awaitAnyTermination()