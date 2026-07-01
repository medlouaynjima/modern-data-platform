from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_expectations.validator.validator import Validator


def apply_fct_daily_sales_expectations(validator: Validator) -> None:
    validator.expect_table_row_count_to_be_between(min_value=1)
    validator.expect_column_values_to_not_be_null("order_date")
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("order_count")
    validator.expect_column_values_to_not_be_null("gross_revenue")
    validator.expect_column_values_to_be_between("order_count", min_value=0)
    validator.expect_column_values_to_be_between("gross_revenue", min_value=0)


def apply_fct_customer_activity_expectations(validator: Validator) -> None:
    validator.expect_table_row_count_to_be_between(min_value=1)
    validator.expect_column_values_to_not_be_null("activity_date")
    validator.expect_column_values_to_not_be_null("customer_id")
    validator.expect_column_values_to_be_between("click_events", min_value=0)
    validator.expect_column_values_to_be_between("orders", min_value=0)
    validator.expect_column_values_to_be_between("revenue", min_value=0)


def apply_fct_inventory_position_expectations(validator: Validator) -> None:
    validator.expect_table_row_count_to_be_between(min_value=1)
    validator.expect_column_values_to_not_be_null("product_id")
    validator.expect_column_values_to_not_be_null("warehouse_id")
    validator.expect_column_values_to_not_be_null("available_quantity")
    validator.expect_compound_columns_to_be_unique(["product_id", "warehouse_id"])


GOLD_SUITE_BUILDERS = {
    "fct_daily_sales": apply_fct_daily_sales_expectations,
    "fct_customer_activity": apply_fct_customer_activity_expectations,
    "fct_inventory_position": apply_fct_inventory_position_expectations,
}
