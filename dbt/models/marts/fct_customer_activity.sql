{{ config(location_root=var("gold_path")) }}

with clicks as (
    select * from {{ ref("stg_clicks") }}
),

orders as (
    select * from {{ ref("int_orders_enriched") }}
),

click_rollup as (
    select
        event_date as activity_date,
        customer_id,
        count(*) as click_events,
        count(distinct session_id) as sessions,
        count(distinct product_id) as products_viewed
    from clicks
    group by event_date, customer_id
),

order_rollup as (
    select
        order_date as activity_date,
        customer_id,
        count(*) as orders,
        sum(quantity) as units_ordered,
        sum(total_amount) as revenue
    from orders
    group by order_date, customer_id
)

select
    coalesce(click_rollup.activity_date, order_rollup.activity_date) as activity_date,
    coalesce(click_rollup.customer_id, order_rollup.customer_id) as customer_id,
    coalesce(click_rollup.click_events, 0) as click_events,
    coalesce(click_rollup.sessions, 0) as sessions,
    coalesce(click_rollup.products_viewed, 0) as products_viewed,
    coalesce(order_rollup.orders, 0) as orders,
    coalesce(order_rollup.units_ordered, 0) as units_ordered,
    coalesce(order_rollup.revenue, 0.0) as revenue
from click_rollup
full outer join order_rollup
    on click_rollup.activity_date = order_rollup.activity_date
    and click_rollup.customer_id = order_rollup.customer_id
