with source as (
    select * from {{ silver_delta("payments") }}
)

select
    event_id,
    event_type,
    payment_id,
    cast(order_id as bigint) as order_id,
    cast(customer_id as bigint) as customer_id,
    cast(amount as double) as payment_amount,
    currency,
    payment_method,
    status as payment_status,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
