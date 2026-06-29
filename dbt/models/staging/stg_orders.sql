with source as (
    select * from {{ silver_delta("orders") }}
)

select
    event_id,
    event_type,
    cast(order_id as bigint) as order_id,
    cast(customer_id as bigint) as customer_id,
    cast(product_id as bigint) as product_id,
    cast(quantity as int) as quantity,
    cast(price as double) as unit_price,
    cast(total_amount as double) as total_amount,
    country,
    channel,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
