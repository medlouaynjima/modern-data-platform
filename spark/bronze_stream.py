from __future__ import annotations

import argparse
import json
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
    quarantine_path: str = "data/bronze/quarantine/events"
    checkpoint_path: str = "data/bronze/_checkpoints/events"
    quarantine_checkpoint_path: str = "data/bronze/_checkpoints/quarantine"
    trigger_available_now: bool = True
    processing_time: str = "30 seconds"
    schema_registry_url: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stream Kafka retail events into Bronze Delta Lake.")
    parser.add_argument("--bootstrap-server", default="localhost:29092")
    parser.add_argument("--topics", default=DEFAULT_TOPICS)
    parser.add_argument("--bronze-path", default="data/bronze/events")
    parser.add_argument("--quarantine-path", default="data/bronze/quarantine/events")
    parser.add_argument("--checkpoint-path", default="data/bronze/_checkpoints/events")
    parser.add_argument(
        "--quarantine-checkpoint-path",
        default="data/bronze/_checkpoints/quarantine",
    )
    parser.add_argument("--schema-registry-url", default=None)
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


def _build_registry(config: BronzeStreamConfig):
    from contracts.registry import SchemaRegistry

    return SchemaRegistry(registry_url=config.schema_registry_url)


def _validate_rows(rows: list[dict], registry) -> tuple[list[dict], list[dict]]:
    from contracts.validator import validate_batch

    valid_rows: list[dict] = []
    quarantine_rows: list[dict] = []

    rows_by_topic: dict[str, list[dict]] = {}
    for row in rows:
        rows_by_topic.setdefault(row["topic"], []).append(row)

    for topic, topic_rows in rows_by_topic.items():
        payloads = []
        for row in topic_rows:
            try:
                payloads.append(json.loads(row["event_payload"]))
            except json.JSONDecodeError:
                payloads.append({})

        results = validate_batch(topic, payloads, registry=registry)
        for row, payload, result in zip(topic_rows, payloads, results):
            if result.valid:
                valid_rows.append(row)
            else:
                quarantine_row = dict(row)
                quarantine_row["validation_errors"] = json.dumps(list(result.errors))
                quarantine_rows.append(quarantine_row)

    return valid_rows, quarantine_rows


def _write_delta_batch(spark, rows: list[dict], path: str, schema, mode: str = "append") -> None:
    if not rows:
        return

    frame = spark.createDataFrame(rows, schema=schema)
    frame.write.format("delta").mode(mode).save(path)


def build_batch_writer(spark, config: BronzeStreamConfig):
    from pyspark.sql.types import StringType, StructField, StructType

    registry = _build_registry(config)

    def process_batch(batch_df: "DataFrame", batch_id: int) -> None:
        if batch_df.isEmpty():
            return

        bronze_schema = batch_df.schema
        quarantine_schema = StructType(
            bronze_schema.fields + [StructField("validation_errors", StringType(), False)]
        )

        rows = [row.asDict(recursive=True) for row in batch_df.collect()]
        valid_rows, quarantine_rows = _validate_rows(rows, registry)

        _write_delta_batch(spark, valid_rows, config.bronze_path, bronze_schema)
        _write_delta_batch(spark, quarantine_rows, config.quarantine_path, quarantine_schema)

        print(
            f"batch {batch_id}: accepted={len(valid_rows)} "
            f"quarantined={len(quarantine_rows)}"
        )

    return process_batch


def write_bronze_stream(spark, bronze_events: "DataFrame", config: BronzeStreamConfig):
    writer = (
        bronze_events.writeStream.foreachBatch(build_batch_writer(spark, config))
        .option("checkpointLocation", config.checkpoint_path)
    )

    if config.trigger_available_now:
        writer = writer.trigger(availableNow=True)
    else:
        writer = writer.trigger(processingTime=config.processing_time)

    return writer.start()


def run(config: BronzeStreamConfig) -> None:
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    kafka_events = read_kafka_stream(spark, config)
    bronze_events = to_bronze_events(kafka_events)
    query = write_bronze_stream(spark, bronze_events, config)
    query.awaitTermination()


def main() -> None:
    args = build_parser().parse_args()
    config = BronzeStreamConfig(
        bootstrap_servers=args.bootstrap_server,
        topics=args.topics,
        bronze_path=args.bronze_path,
        quarantine_path=args.quarantine_path,
        checkpoint_path=args.checkpoint_path,
        quarantine_checkpoint_path=args.quarantine_checkpoint_path,
        trigger_available_now=not args.continuous,
        processing_time=args.processing_time,
        schema_registry_url=args.schema_registry_url,
    )
    run(config)


if __name__ == "__main__":
    main()
