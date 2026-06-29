{{ config(location_root=var("gold_path")) }}

with orders as (
    select * from {{ ref("int_orders_enriched") }}
)

select
    order_date,
    product_id,
    sku,
    product_name,
    category,
    country,
    channel,
    count(*) as order_count,
    count(distinct customer_id) as customer_count,
    sum(quantity) as units_sold,
    sum(total_amount) as gross_revenue,
    sum(gross_margin) as gross_margin,
    sum(payment_amount) as collected_payment_amount,
    sum(has_authorized_payment) as authorized_payment_count
from orders
group by
    order_date,
    product_id,
    sku,
    product_name,
    category,
    country,
    channel
