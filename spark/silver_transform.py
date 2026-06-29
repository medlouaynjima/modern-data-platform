from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql.types import DataType, StructType


DEFAULT_BRONZE_PATH = "data/bronze/events"
DEFAULT_SILVER_PATH = "data/silver"
DEFAULT_TOPICS = ("customers", "products", "orders", "payments", "clicks", "inventory")

COMMON_PAYLOAD_FIELDS = (
    ("event_id", "string"),
    ("event_type", "string"),
    ("timestamp", "string"),
)

TOPIC_PAYLOAD_FIELDS = {
    "customers": (
        ("customer_id", "long"),
        ("name", "string"),
        ("email", "string"),
        ("country", "string"),
        ("signup_date", "date"),
        ("loyalty_tier", "string"),
    ),
    "products": (
        ("product_id", "long"),
        ("sku", "string"),
        ("name", "string"),
        ("category", "string"),
        ("price", "double"),
        ("cost", "double"),
        ("active", "boolean"),
    ),
    "orders": (
        ("order_id", "long"),
        ("customer_id", "long"),
        ("product_id", "long"),
        ("quantity", "integer"),
        ("price", "double"),
        ("total_amount", "double"),
        ("country", "string"),
        ("channel", "string"),
    ),
    "payments": (
        ("payment_id", "string"),
        ("order_id", "long"),
        ("customer_id", "long"),
        ("amount", "double"),
        ("currency", "string"),
        ("payment_method", "string"),
        ("status", "string"),
    ),
    "clicks": (
        ("session_id", "string"),
        ("customer_id", "long"),
        ("product_id", "long"),
        ("device", "string"),
        ("country", "string"),
        ("referrer", "string"),
    ),
    "inventory": (
        ("inventory_event_id", "string"),
        ("product_id", "long"),
        ("warehouse_id", "string"),
        ("quantity_delta", "integer"),
        ("available_quantity", "integer"),
        ("reason", "string"),
    ),
}

LINEAGE_COLUMNS = (
    "source_topic",
    "source_partition",
    "source_offset",
    "kafka_timestamp",
    "kafka_timestamp_type",
    "event_key",
    "bronze_ingested_at",
    "bronze_ingest_date",
    "silver_processed_at",
)


@dataclass(frozen=True)
class SilverTransformConfig:
    bronze_path: str = DEFAULT_BRONZE_PATH
    silver_path: str = DEFAULT_SILVER_PATH
    topics: tuple[str, ...] = DEFAULT_TOPICS
    write_mode: str = "overwrite"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transform Bronze retail events into typed Silver Delta tables.")
    parser.add_argument("--bronze-path", default=DEFAULT_BRONZE_PATH)
    parser.add_argument("--silver-path", default=DEFAULT_SILVER_PATH)
    parser.add_argument(
        "--topics",
        default=",".join(DEFAULT_TOPICS),
        help="Comma-separated topics to transform.",
    )
    parser.add_argument(
        "--write-mode",
        default="overwrite",
        choices=("overwrite", "append"),
        help="Delta write mode for each Silver table.",
    )
    return parser


def create_spark_session(app_name: str = "mdp-silver-transform") -> "SparkSession":
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "6")
        .getOrCreate()
    )


def payload_fields_for_topic(topic: str) -> tuple[tuple[str, str], ...]:
    if topic not in TOPIC_PAYLOAD_FIELDS:
        raise ValueError(f"Unknown topic: {topic}")

    return COMMON_PAYLOAD_FIELDS + TOPIC_PAYLOAD_FIELDS[topic]


def payload_schema_for_topic(topic: str) -> "StructType":
    from pyspark.sql.types import (
        BooleanType,
        DateType,
        DoubleType,
        IntegerType,
        LongType,
        StringType,
        StructField,
        StructType,
    )

    type_map: dict[str, "DataType"] = {
        "boolean": BooleanType(),
        "date": DateType(),
        "double": DoubleType(),
        "integer": IntegerType(),
        "long": LongType(),
        "string": StringType(),
    }

    return StructType(
        [StructField(name, type_map[type_name], nullable=True) for name, type_name in payload_fields_for_topic(topic)]
    )


def parse_topics(value: str) -> tuple[str, ...]:
    topics = tuple(topic.strip() for topic in value.split(",") if topic.strip())
    unknown_topics = [topic for topic in topics if topic not in TOPIC_PAYLOAD_FIELDS]

    if unknown_topics:
        raise ValueError(f"Unknown topics: {', '.join(unknown_topics)}")

    return topics


def read_bronze_events(spark: "SparkSession", bronze_path: str) -> "DataFrame":
    return spark.read.format("delta").load(bronze_path)


def to_silver_table(bronze_events: "DataFrame", topic: str) -> "DataFrame":
    from pyspark.sql.functions import col, current_timestamp, from_json, to_date, to_timestamp

    schema = payload_schema_for_topic(topic)
    payload_columns = [field_name for field_name, _ in payload_fields_for_topic(topic) if field_name != "timestamp"]

    parsed = (
        bronze_events.filter(col("topic") == topic)
        .withColumn("payload", from_json(col("event_payload"), schema))
        .filter(col("payload.event_id").isNotNull())
    )

    selected_payload_columns = [col(f"payload.{field_name}").alias(field_name) for field_name in payload_columns]

    return (
        parsed.select(
            *selected_payload_columns,
            to_timestamp(col("payload.timestamp")).alias("event_timestamp"),
            col("topic").alias("source_topic"),
            col("partition").alias("source_partition"),
            col("offset").alias("source_offset"),
            col("kafka_timestamp"),
            col("kafka_timestamp_type"),
            col("event_key"),
            col("ingested_at").alias("bronze_ingested_at"),
            col("ingest_date").alias("bronze_ingest_date"),
            current_timestamp().alias("silver_processed_at"),
        )
        .withColumn("event_date", to_date(col("event_timestamp")))
        .dropDuplicates(["event_id", "source_topic", "source_partition", "source_offset"])
    )


def silver_table_path(silver_path: str, topic: str) -> str:
    return f"{silver_path.rstrip('/')}/{topic}"


def write_silver_table(table: "DataFrame", silver_path: str, topic: str, mode: str) -> None:
    (
        table.write.format("delta")
        .mode(mode)
        .option("overwriteSchema", "true")
        .partitionBy("event_date")
        .save(silver_table_path(silver_path, topic))
    )


def run(config: SilverTransformConfig) -> None:
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    bronze_events = read_bronze_events(spark, config.bronze_path)
    for topic in config.topics:
        silver_table = to_silver_table(bronze_events, topic)
        row_count = silver_table.count()
        write_silver_table(silver_table, config.silver_path, topic, config.write_mode)
        print(f"Wrote {row_count} rows to {silver_table_path(config.silver_path, topic)}")


def main() -> None:
    args = build_parser().parse_args()
    config = SilverTransformConfig(
        bronze_path=args.bronze_path,
        silver_path=args.silver_path,
        topics=parse_topics(args.topics),
        write_mode=args.write_mode,
    )
    run(config)


if __name__ == "__main__":
    main()
