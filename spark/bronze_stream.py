from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


DEFAULT_TOPICS = "customers,products,orders,payments,clicks,inventory"


@dataclass(frozen=True)
class BronzeStreamConfig:
    bootstrap_servers: str = "localhost:29092"
    topics: str = DEFAULT_TOPICS
    bronze_path: str = "data/bronze/events"
    checkpoint_path: str = "data/bronze/_checkpoints/events"
    trigger_available_now: bool = True
    processing_time: str = "30 seconds"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stream Kafka retail events into Bronze Delta Lake.")
    parser.add_argument("--bootstrap-server", default="localhost:29092")
    parser.add_argument("--topics", default=DEFAULT_TOPICS)
    parser.add_argument("--bronze-path", default="data/bronze/events")
    parser.add_argument("--checkpoint-path", default="data/bronze/_checkpoints/events")
    parser.add_argument(
        "--processing-time",
        default="30 seconds",
        help="Processing-time trigger used when --continuous is set.",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Keep streaming instead of using Spark's availableNow trigger.",
    )
    return parser


def create_spark_session(app_name: str = "mdp-bronze-stream") -> "SparkSession":
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "6")
        .getOrCreate()
    )


def read_kafka_stream(spark: "SparkSession", config: BronzeStreamConfig) -> "DataFrame":
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", config.bootstrap_servers)
        .option("subscribe", config.topics)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )


def to_bronze_events(kafka_events: "DataFrame") -> "DataFrame":
    from pyspark.sql.functions import col, current_timestamp, to_date

    return (
        kafka_events.select(
            col("topic"),
            col("partition"),
            col("offset"),
            col("timestamp").alias("kafka_timestamp"),
            col("timestampType").alias("kafka_timestamp_type"),
            col("key").cast("string").alias("event_key"),
            col("value").cast("string").alias("event_payload"),
        )
        .withColumn("ingested_at", current_timestamp())
        .withColumn("ingest_date", to_date(col("ingested_at")))
    )


def write_bronze_stream(bronze_events: "DataFrame", config: BronzeStreamConfig):
    writer = (
        bronze_events.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", config.checkpoint_path)
        .partitionBy("topic", "ingest_date")
    )

    if config.trigger_available_now:
        writer = writer.trigger(availableNow=True)
    else:
        writer = writer.trigger(processingTime=config.processing_time)

    return writer.start(config.bronze_path)


def run(config: BronzeStreamConfig) -> None:
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    kafka_events = read_kafka_stream(spark, config)
    bronze_events = to_bronze_events(kafka_events)
    query = write_bronze_stream(bronze_events, config)
    query.awaitTermination()


def main() -> None:
    args = build_parser().parse_args()
    config = BronzeStreamConfig(
        bootstrap_servers=args.bootstrap_server,
        topics=args.topics,
        bronze_path=args.bronze_path,
        checkpoint_path=args.checkpoint_path,
        trigger_available_now=not args.continuous,
        processing_time=args.processing_time,
    )
    run(config)


if __name__ == "__main__":
    main()
