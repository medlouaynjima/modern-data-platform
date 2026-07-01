from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_expectations.validator.validator import Validator


def apply_common_silver_expectations(validator: Validator) -> None:
    validator.expect_table_row_count_to_be_between(min_value=1)
    validator.expect_column_values_to_not_be_null("event_id")
    validator.expect_column_values_to_not_be_null("event_type")
    validator.expect_column_values_to_not_be_null("event_timestamp")
    validator.expect_compound_columns_to_be_unique(
        ["event_id", "source_topic", "source_partition", "source_offset"]
    )


def apply_customers_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_not_be_null("email")
    validator.expect_column_values_to_not_be_null("country")


def apply_products_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("sku")
    validator.expect_column_values_to_be_between("price", min_value=0)


def apply_orders_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("order_id")
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_be_between("total_amount", min_value=0)
    validator.expect_column_values_to_be_between("quantity", min_value=1)


def apply_payments_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("payment_id")
    validator.expect_column_values_to_not_be_null("order_id")
    validator.expect_column_values_to_be_between("amount", min_value=0)
    validator.expect_column_values_to_be_in_set(
        "status",
        value_set=["authorized", "declined", "refunded"],
    )


def apply_clicks_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("session_id")
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_not_be_null("product_id")


def apply_inventory_expectations(validator: Validator) -> None:
    apply_common_silver_expectations(validator)
    validator.expect_column_values_to_not_be_null("inventory_event_id")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("warehouse_id")
    validator.expect_column_values_to_not_be_null("available_quantity")


SILVER_SUITE_BUILDERS = {
    "customers": apply_customers_expectations,
    "products": apply_products_expectations,
    "orders": apply_orders_expectations,
    "payments": apply_payments_expectations,
    "clicks": apply_clicks_expectations,
    "inventory": apply_inventory_expectations,
}
