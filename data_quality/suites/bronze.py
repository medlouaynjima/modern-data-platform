from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_expectations.validator.validator import Validator

RETAIL_TOPICS = (
    "customers",
    "products",
    "orders",
    "payments",
    "clicks",
    "inventory",
)


def apply_bronze_events_expectations(validator: Validator) -> None:
    validator.expect_table_row_count_to_be_between(min_value=1)
    validator.expect_column_values_to_not_be_null("topic")
    validator.expect_column_values_to_not_be_null("partition")
    validator.expect_column_values_to_not_be_null("offset")
    validator.expect_column_values_to_not_be_null("event_key")
    validator.expect_column_values_to_not_be_null("event_payload")
    validator.expect_column_values_to_not_be_null("ingested_at")
    validator.expect_column_values_to_be_in_set("topic", value_set=list(RETAIL_TOPICS))
    validator.expect_compound_columns_to_be_unique(["topic", "partition", "offset"])


BRONZE_SUITE_BUILDERS = {
    "events": apply_bronze_events_expectations,
}
