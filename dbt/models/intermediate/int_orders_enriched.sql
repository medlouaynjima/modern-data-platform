with orders as (
    select * from {{ ref("stg_orders") }}
),

products as (
    select * from {{ ref("stg_products") }}
),

payments as (
    select * from {{ ref("stg_payments") }}
),

ranked_products as (
    select
        *,
        row_number() over (
            partition by product_id
            order by event_timestamp desc, source_offset desc
        ) as product_rank
    from products
),

payment_rollup as (
    select
        order_id,
        count(*) as payment_events,
        sum(payment_amount) as payment_amount,
        max(case when payment_status = 'authorized' then 1 else 0 end) as has_authorized_payment,
        max(event_timestamp) as latest_payment_timestamp
    from payments
    group by order_id
)

select
    orders.order_id,
    orders.event_id as order_event_id,
    orders.customer_id,
    orders.product_id,
    ranked_products.sku,
    ranked_products.product_name,
    ranked_products.category,
    orders.quantity,
    orders.unit_price,
    orders.total_amount,
    cast(orders.total_amount - (coalesce(ranked_products.cost, 0.0) * orders.quantity) as double) as gross_margin,
    orders.country,
    orders.channel,
    coalesce(payment_rollup.payment_events, 0) as payment_events,
    coalesce(payment_rollup.payment_amount, 0.0) as payment_amount,
    coalesce(payment_rollup.has_authorized_payment, 0) as has_authorized_payment,
    payment_rollup.latest_payment_timestamp,
    orders.event_timestamp as order_timestamp,
    orders.event_date as order_date
from orders
left join ranked_products
    on orders.product_id = ranked_products.product_id
    and ranked_products.product_rank = 1
left join payment_rollup
    on orders.order_id = payment_rollup.order_id
