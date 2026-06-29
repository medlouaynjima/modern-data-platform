import pytest

from spark.silver_transform import (
    DEFAULT_TOPICS,
    LINEAGE_COLUMNS,
    SilverTransformConfig,
    parse_topics,
    payload_fields_for_topic,
    silver_table_path,
)


def test_silver_config_defaults_to_bronze_and_silver_layers():
    config = SilverTransformConfig()

    assert config.bronze_path == "data/bronze/events"
    assert config.silver_path == "data/silver"
    assert config.topics == DEFAULT_TOPICS
    assert config.write_mode == "overwrite"


def test_all_silver_topics_have_common_payload_fields():
    for topic in DEFAULT_TOPICS:
        fields = [field_name for field_name, _ in payload_fields_for_topic(topic)]

        assert fields[:3] == ["event_id", "event_type", "timestamp"]


def test_silver_topic_contracts_include_business_keys():
    expected_keys = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "payments": "payment_id",
        "clicks": "session_id",
        "inventory": "inventory_event_id",
    }

    for topic, key in expected_keys.items():
        fields = [field_name for field_name, _ in payload_fields_for_topic(topic)]

        assert key in fields


def test_lineage_columns_are_preserved_for_silver_tables():
    assert LINEAGE_COLUMNS == (
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


def test_parse_topics_rejects_unknown_topics():
    with pytest.raises(ValueError, match="Unknown topics: refunds"):
        parse_topics("orders,refunds")


def test_silver_table_paths_are_topic_scoped():
    assert silver_table_path("data/silver", "orders") == "data/silver/orders"
    assert silver_table_path("data/silver/", "orders") == "data/silver/orders"
